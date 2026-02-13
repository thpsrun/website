from typing import TYPE_CHECKING, Any

from django.core.cache import caches
from django.db.models import QuerySet
from django.db.models.functions import TruncDate
from srl.models import Runs

from api.v1.routers.utils import (
    main_pbs_cache_key,
    main_records_cache_key,
    main_wrs_cache_key,
)

TIMEOUT = 604800

if TYPE_CHECKING:
    from srl.models import RunPlayers


def player_data_export(
    run_players: "QuerySet[RunPlayers]",
) -> list[dict[str, str | None]]:
    players = [
        {
            "name": rp.player.nickname if rp.player.nickname else rp.player.name,
            "country": rp.player.countrycode.name if rp.player.countrycode else None,
        }
        for rp in run_players
    ]
    return players if players else [{"name": "Anonymous", "country": None}]


def record_player_data_export(
    run_players: "QuerySet[RunPlayers]",
    run_url: str,
    run_date: str | None,
) -> list[dict[str, Any]]:
    players = [
        {
            "player": {
                "name": rp.player.nickname if rp.player.nickname else rp.player.name,
                "country": (
                    rp.player.countrycode.name if rp.player.countrycode else None
                ),
            },
            "url": run_url,
            "date": run_date,
        }
        for rp in run_players
    ]
    if not players:
        players = [
            {
                "player": {"name": "Anonymous", "country": None},
                "url": run_url,
                "date": run_date,
            }
        ]
    return players


def query_latest_runs(
    wr: bool = True,
) -> list[dict[str, Any]]:
    filters = {
        "obsolete": False,
        "v_date__isnull": False,
        "vid_status": "verified",
    }

    if wr:
        filters["place"] = 1
    else:
        filters["place__gt"] = 1

    runs: QuerySet[Runs] = (
        Runs.objects.select_related("game", "category")
        .prefetch_related("run_players__player__countrycode")
        .filter(**filters)
        .order_by("-v_date")[:5]
    )

    result = []
    for run in runs:
        players_data = player_data_export(run.run_players.all())  # type: ignore
        result.append(
            {
                "id": run.id,
                "game": {"name": run.game.name, "slug": run.game.slug},
                "category": ({"name": run.category.name} if run.category else None),
                "subcategory": run.subcategory,
                "players": players_data,
                "time": run.time,
                "date": run.v_date.isoformat() if run.v_date else None,
                "video": run.video,
                "url": run.url,
            }
        )
    return result


def query_records() -> list[dict[str, Any]]:
    runs: list[Runs] = list(
        Runs.objects.select_related("game", "category")
        .prefetch_related("run_players__player__countrycode")
        .filter(
            runtype="main",
            place=1,
            obsolete=False,
            vid_status="verified",
            category__appear_on_main=True,
        )
        .exclude(
            runvariablevalues__value__appear_on_main=False,
        )
        .order_by("-subcategory")
        .annotate(o_date=TruncDate("date"))
    )

    grouped_runs: list[dict[str, Any]] = []
    seen_records: set[tuple[str, str | None, float | None]] = set()

    for run in runs:
        key = (run.game.slug, run.subcategory, run.time)
        if key not in seen_records:
            grouped_runs.append(
                {
                    "game": {"name": run.game.name, "slug": run.game.slug},
                    "game_release": run.game.release,
                    "subcategory": run.subcategory,
                    "time": run.time,
                    "players": [],
                }
            )
            seen_records.add(key)

        for record in grouped_runs:
            if (
                record["game"]["slug"] == run.game.slug
                and record["subcategory"] == run.subcategory
                and record["time"] == run.time
            ):
                record["players"].extend(
                    record_player_data_export(
                        run.run_players.all(),  # type: ignore
                        run.url,
                        run.o_date.isoformat() if run.o_date else None,  # type: ignore
                    )
                )

    run_list = sorted(
        grouped_runs,
        key=lambda x: x["game_release"],
        reverse=False,
    )

    # Remove the sorting helper field before returning
    for record in run_list:
        del record["game_release"]

    return run_list


def get_cached_embed(
    embed_type: str,
    cache_name: str = "default",
) -> list[dict[str, Any]]:
    """Fetch embed data from cache or query database.

    Each embed type is cached independently for maximum reuse.
    """
    key_functions = {
        "latest-wrs": main_wrs_cache_key,
        "latest-pbs": main_pbs_cache_key,
        "records": main_records_cache_key,
    }
    query_functions: dict[str, Any] = {
        "latest-wrs": lambda: query_latest_runs(wr=True),
        "latest-pbs": lambda: query_latest_runs(wr=False),
        "records": query_records,
    }

    cache = caches[cache_name]
    cache_key = key_functions[embed_type]()

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = query_functions[embed_type]()
    cache.set(cache_key, result, timeout=TIMEOUT)  # 7 days in seconds

    return result
