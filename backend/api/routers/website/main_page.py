from typing import Any, Dict, Optional, Union

from django.db.models.functions import TruncDate
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Runs

from api.permissions import public_auth
from api.schemas.base import ErrorResponse

main_page_router = Router(tags=["Website - Main Page"])


@main_page_router.get(
    "/main",
    response=Union[Dict[str, Any], ErrorResponse],
    summary="Get Main Page Data",
    description="""
    Get aggregated data for the website main page including latest world records,
    personal bests, and current records for featured categories.

    **Query Parameters:**
    - `data`: Comma-separated list of data types to include
      - `latest-wrs`: Latest 5 world records
      - `latest-pbs`: Latest 5 personal bests (excluding WRs)
      - `records`: Current WRs for featured categories

    **Examples:**
    - `/website/main?data=latest-wrs,latest-pbs` - Recent activity
    - `/website/main?data=records` - Current world records
    - `/website/main?data=latest-wrs,latest-pbs,records` - All data

    **Improvements over DRF:**
    - Renamed 'query' param to 'data' for clarity
    - Better error messages
    - Optimized database queries
    """,
    auth=public_auth,
)
def get_main_page_data(
    request: HttpRequest,
    data: Optional[str] = Query(None, description="Comma-separated data types"),
) -> Union[Dict[str, Any], ErrorResponse]:
    """Get main page data with flexible data selection."""
    if not data:
        return ErrorResponse(
            error="Must specify data types to retrieve",
            details={"valid_data_types": ["latest-wrs", "latest-pbs", "records"]},
            code=400,
        )

    data_fields = [field.strip() for field in data.split(",") if field.strip()]
    valid_data_types = {"latest-wrs", "latest-pbs", "records"}
    invalid_data = [field for field in data_fields if field not in valid_data_types]

    if invalid_data:
        return ErrorResponse(
            error=f"Invalid data type(s): {', '.join(invalid_data)}",
            details={"valid_data_types": list(valid_data_types)},
            code=400,
        )

    try:
        response_data = {}

        if "latest-wrs" in data_fields:
            wrs: Runs = (
                Runs.objects.exclude(vid_status__in=["new", "rejected"])
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(place=1, obsolete=False, v_date__isnull=False)
                .order_by("-v_date")[:5]
            )

            response_data["latest_wrs"] = []
            for run in wrs:
                run_players = run.run_players.select_related(
                    "player__countrycode"
                ).order_by("order")

                players_data = []
                for rp in run_players:
                    players_data.append(
                        {
                            "name": (
                                rp.player.nickname
                                if rp.player.nickname
                                else rp.player.name
                            ),
                            "country": (
                                rp.player.countrycode.name
                                if rp.player.countrycode
                                else None
                            ),
                        }
                    )

                response_data["latest_wrs"].append(
                    {
                        "id": run.id,
                        "game": {"name": run.game.name, "slug": run.game.slug},
                        "category": (
                            {"name": run.category.name} if run.category else None
                        ),
                        "subcategory": run.subcategory,
                        "players": (
                            players_data
                            if players_data
                            else [{"name": "Anonymous", "country": None}]
                        ),
                        "time": run.time,
                        "date": run.v_date.isoformat() if run.v_date else None,
                        "video": run.video,
                        "url": run.url,
                    }
                )

        if "latest-pbs" in data_fields:
            pbs: Runs = (
                Runs.objects.exclude(vid_status__in=["new", "rejected"])
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(place__gt=1, obsolete=False, v_date__isnull=False)
                .order_by("-v_date")[:5]
            )

            response_data["latest_pbs"] = []
            for run in pbs:
                run_players = run.run_players.select_related(
                    "player__countrycode"
                ).order_by("order")

                players_data = []
                for rp in run_players:
                    players_data.append(
                        {
                            "name": (
                                rp.player.nickname
                                if rp.player.nickname
                                else rp.player.name
                            ),
                            "country": (
                                rp.player.countrycode.name
                                if rp.player.countrycode
                                else None
                            ),
                        }
                    )

                response_data["latest_pbs"].append(
                    {
                        "id": run.id,
                        "game": {"name": run.game.name, "slug": run.game.slug},
                        "category": (
                            {"name": run.category.name} if run.category else None
                        ),
                        "subcategory": run.subcategory,
                        "players": (
                            players_data
                            if players_data
                            else [{"name": "Anonymous", "country": None}]
                        ),
                        "time": run.time,
                        "place": run.place,
                        "date": run.v_date.isoformat() if run.v_date else None,
                        "video": run.video,
                        "url": run.url,
                    }
                )

        if "records" in data_fields:
            runs = list(
                Runs.objects.exclude(vid_status__in=["new", "rejected"], obsolete=True)
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(
                    runtype="main",
                    place=1,
                    category__appear_on_main=True,
                )
                .order_by("-subcategory")
                .annotate(o_date=TruncDate("date"))
            )

            best_runs = {}
            for run in runs:
                if run.game.defaulttime == "realtime":
                    time_val = run.time_secs
                elif run.game.defaulttime == "realtime_noloads":
                    time_val = run.timenl_secs
                else:
                    time_val = run.timeigt_secs

                key = (run.game.id, run.category.id)
                if key not in best_runs or time_val < best_runs[key][0]:
                    best_runs[key] = (time_val, run)

            runs_list = [r[1] for r in best_runs.values()]

            grouped_runs = []
            seen_records = set()

            for run in runs_list:
                key = (run.game.slug, run.subcategory, run.time)
                if key not in seen_records:
                    grouped_runs.append(
                        {
                            "game": {
                                "name": run.game.name,
                                "slug": run.game.slug,
                                "release": run.game.release.isoformat(),
                            },
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
                        run_players = run.run_players.select_related(
                            "player__countrycode"
                        ).order_by("order")

                        players_data = []
                        for rp in run_players:
                            players_data.append(
                                {
                                    "player": {
                                        "name": (
                                            rp.player.nickname
                                            if rp.player.nickname
                                            else rp.player.name
                                        ),
                                        "country": (
                                            rp.player.countrycode.name
                                            if rp.player.countrycode
                                            else None
                                        ),
                                    },
                                    "url": run.url,
                                    "date": (
                                        run.o_date.isoformat()
                                        if hasattr(run, "o_date") and run.o_date
                                        else None
                                    ),
                                }
                            )

                        if not players_data:
                            players_data = [
                                {
                                    "player": {"name": "Anonymous", "country": None},
                                    "url": run.url,
                                    "date": (
                                        run.o_date.isoformat()
                                        if hasattr(run, "o_date") and run.o_date
                                        else None
                                    ),
                                }
                            ]

                        record["players"].extend(players_data)

            response_data["records"] = sorted(
                grouped_runs, key=lambda x: x["game"]["release"]
            )

        return response_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve main page data",
            details={"exception": str(e)},
            code=500,
        )
