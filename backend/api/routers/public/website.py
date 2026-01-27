from textwrap import dedent
from typing import TYPE_CHECKING, Annotated, Any

from django.db.models import Case, IntegerField, Prefetch, Q, QuerySet, Value, When
from django.db.models.functions import TruncDate
from django.http import HttpRequest
from ninja import Path, Query, Router
from ninja.responses import codes_4xx
from pydantic import Field
from srl.models import Categories, Games, Levels, Runs, Variables

from api.docs.website import GAME_CATEGORIES_GET, GAME_LEVELS_GET, MAIN_PAGE_GET
from api.ordering import get_ordered_level_names
from api.permissions import public_auth
from api.schemas.base import ErrorResponse

if TYPE_CHECKING:
    from srl.models import RunPlayers

router = Router()


def player_data_export(
    run_players: "QuerySet[RunPlayers]",
) -> list[dict[str, str | None]]:
    """Build basic player data list from run_players queryset.

    Returns a list of dicts with 'name' and 'country' keys.
    Falls back to Anonymous if no players exist.
    """
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
    """Build player data for records with run URL and date.

    Returns a list of dicts with nested 'player' object plus 'url' and 'date'.
    Falls back to Anonymous if no players exist.
    """
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


@router.get(
    "/main",
    response={200: dict[str, Any], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Main Page Data",
    description=dedent(
        """
    Get aggregated data for the website main page including latest world records,
    personal bests, and current records for featured categories.

    **Supported Data Types:**
    - `latest-wrs`: Latest 5 world records
    - `latest-pbs`: Latest 5 personal bests (excluding WRs)
    - `records`: Current WRs for featured categories

    **Supported Parameters:**
    - `embed`: Comma-separated list of data types to include (required)

    **Examples:**
    - `/website/main?embed=latest-wrs,latest-pbs` - Recent activity
    - `/website/main?embed=records` - Current world records
    - `/website/main?embed=latest-wrs,latest-pbs,records` - All data

    **Note:** This is an aggregation endpoint optimized for the React frontend homepage.
    """
    ),
    auth=public_auth,
    openapi_extra=MAIN_PAGE_GET,
)
def get_main_page_data(
    request: HttpRequest,
    embed: Annotated[
        str | None,
        Query,
        Field(description="Comma-separated embed types"),
    ] = None,
) -> tuple[int, dict[str, Any] | ErrorResponse]:
    """Get main page data with flexible embed selection."""
    if not embed:
        return 400, ErrorResponse(
            error="Must specify embed types to retrieve",
            details={"valid_embed_types": ["latest-wrs", "latest-pbs", "records"]},
        )

    embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
    valid_embed_types = {"latest-wrs", "latest-pbs", "records"}
    invalid_embeds = [field for field in embed_fields if field not in valid_embed_types]

    if invalid_embeds:
        return 400, ErrorResponse(
            error=f"Invalid embed type(s): {', '.join(invalid_embeds)}",
            details={"valid_embed_types": list(valid_embed_types)},
        )

    try:
        response_data = {}

        if "latest-wrs" in embed_fields:
            wrs: QuerySet[Runs] = (
                Runs.objects.exclude(vid_status__in=["new", "rejected"])
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(place=1, obsolete=False, v_date__isnull=False)
                .order_by("-v_date")[:5]
            )

            response_data["latest_wrs"] = []
            for run in wrs:
                players_data = player_data_export(run.run_players.all())

                response_data["latest_wrs"].append(
                    {
                        "id": run.id,
                        "game": {"name": run.game.name, "slug": run.game.slug},
                        "category": (
                            {"name": run.category.name} if run.category else None
                        ),
                        "subcategory": run.subcategory,
                        "players": players_data,
                        "time": run.time,
                        "date": run.v_date.isoformat() if run.v_date else None,
                        "video": run.video,
                        "url": run.url,
                    }
                )

        if "latest-pbs" in embed_fields:
            pbs: QuerySet[Runs] = (
                Runs.objects.exclude(vid_status__in=["new", "rejected"])
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(place__gt=1, obsolete=False, v_date__isnull=False)
                .order_by("-v_date")[:5]
            )

            response_data["latest_pbs"] = []
            for run in pbs:
                players_data = player_data_export(run.run_players.all())

                response_data["latest_pbs"].append(
                    {
                        "id": run.id,
                        "game": {"name": run.game.name, "slug": run.game.slug},
                        "category": (
                            {"name": run.category.name} if run.category else None
                        ),
                        "subcategory": run.subcategory,
                        "players": players_data,
                        "time": run.time,
                        "place": run.place,
                        "date": run.v_date.isoformat() if run.v_date else None,
                        "video": run.video,
                        "url": run.url,
                    }
                )

        if "records" in embed_fields:
            runs = list(
                Runs.objects.exclude(
                    Q(vid_status__in=["new", "rejected"]) | Q(obsolete=True)
                )
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

            # Finds the single best run for each game/category combination.
            # Uses the game's default timing method to compare times and keeps only the
            # fastest run (by time value) for each unique (game_id, category_id) pair.
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
                        run_date = (
                            run.o_date.isoformat()
                            if hasattr(run, "o_date") and run.o_date
                            else None
                        )
                        players_data = record_player_data_export(
                            run.run_players.all(),
                            run.url,
                            run_date,
                        )
                        record["players"].extend(players_data)

            response_data["records"] = sorted(
                grouped_runs, key=lambda x: x["game"]["release"]
            )

        return 200, response_data

    except Exception as e:
        return 500, ErrorResponse(
            error="Failed to retrieve main page data",
            details={"exception": str(e)},
        )


@router.get(
    "/game/{game_id}/categories",
    response={200: list[dict[str, Any]], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Game Categories with Variables",
    description=dedent(
        """
    Get all categories for a game with their variables and values.
    Optimized for the category selection interface.

    **Features:**
    - Custom category ordering (Any%, 100%, etc. prioritized)
    - Includes all variables with their possible values
    - Optimized database queries with prefetch

    **Examples:**
    - `/website/game/thps4/categories` - Get all THPS4 categories
    - `/website/game/n2680o1p/categories` - Get categories by game ID

    **Note:** This is an aggregation endpoint optimized for the React frontend game page.
    Returns categories with embedded variables and values in a single request.
    """
    ),
    auth=public_auth,
    openapi_extra=GAME_CATEGORIES_GET,
)
def get_game_categories(
    request: HttpRequest,
    game_id: Annotated[
        str,
        Path(
            ...,
            description="Game ID or slug",
        ),
    ],
) -> tuple[int, list[dict[str, Any]] | ErrorResponse]:
    """Get categories for a game with variables."""
    if len(game_id) > 15:
        return 400, ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
        )

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return 404, ErrorResponse(
                error="Game not found",
                details=None,
            )

        # Orders categories by a priority system for consistent display across the site.
        # Common category types (Any%, 100%, etc.) are sorted to top with specific order,
        # while other categories fall back to alphabetical sorting.
        categories = (
            Categories.objects.filter(game=game)
            .annotate(
                order=Case(
                    When(name__istartswith="Any%", then=Value(1)),
                    When(name__istartswith="All Goals & Golds", then=Value(2)),
                    When(name__istartswith="Story", then=Value(3)),
                    When(name__istartswith="Classic", then=Value(4)),
                    When(name__istartswith="0%", then=Value(5)),
                    When(name__istartswith="100%", then=Value(7)),
                    default=Value(6),
                    output_field=IntegerField(),
                )
            )
            .order_by("order", "name")
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related("variablevalues_set"),
                )
            )
        )

        # Convert to response format
        categories_data = []
        for category in categories:
            variables_data = []
            for variable in category.variables_set.all():
                values_data = [
                    {
                        "value": val.value,
                        "name": val.name,
                        "slug": val.slug,
                        "archive": val.archive,
                        "rules": val.rules,
                    }
                    for val in variable.variablevalues_set.all()
                ]

                variables_data.append(
                    {
                        "id": variable.id,
                        "name": variable.name,
                        "slug": variable.slug,
                        "scope": variable.scope,
                        "all_cats": (variable.cat is None),
                        "archive": variable.archive,
                        "values": values_data,
                    }
                )

            categories_data.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "type": category.type,
                    "url": category.url,
                    "rules": category.rules,
                    "appear_on_main": category.appear_on_main,
                    "archive": category.archive,
                    "variables": variables_data,
                }
            )

        return 200, categories_data

    except Exception as e:
        return 500, ErrorResponse(
            error="Failed to retrieve game categories",
            details={"exception": str(e)},
        )


@router.get(
    "/game/{game_id}/levels",
    response={200: list[dict[str, Any]], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Game Levels with Variables",
    description=dedent(
        """
    Get all levels for a game with their variables and values.
    Used for Individual Level (IL) speedrun interfaces.

    **Features:**
    - Custom level ordering using existing ordering system
    - Includes level-specific variables with their possible values
    - Optimized database queries with prefetch

    **Examples:**
    - `/website/game/thps4/levels` - Get all THPS4 levels
    - `/website/game/n2680o1p/levels` - Get levels by game ID

    **Note:** This is an aggregation endpoint optimized for the React frontend IL page.
    Returns levels with embedded variables and values in a single request.
    """
    ),
    auth=public_auth,
    openapi_extra=GAME_LEVELS_GET,
)
def get_game_levels(
    request: HttpRequest,
    game_id: Annotated[
        str,
        Path(
            ...,
            description="Game ID or slug",
        ),
    ],
) -> tuple[int, list[dict[str, Any]] | ErrorResponse]:
    """Get levels for a game with variables (converted from Web_Levels.py)."""
    if len(game_id) > 15:
        return 400, ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
        )

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return 404, ErrorResponse(
                error="Game not found",
                details=None,
            )

        # Orders levels using a game-specific ordering system. The `get_ordered_level_names`
        # function returns levels in the canonical order for each game (e.g., story order
        # or difficulty progression), falling back to alphabetical if no custom order exists.
        get_order = get_ordered_level_names(game.slug)
        level_order = Case(
            *(When(name=name, then=position) for position, name in enumerate(get_order))
        )

        levels = (
            Levels.objects.filter(game=game)
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related("variablevalues_set"),
                )
            )
            .order_by(level_order)
        )

        # Convert to response format
        levels_data = []
        for level in levels:
            variables_data = []
            for variable in level.variables_set.all():
                values_data = [
                    {
                        "value": val.value,
                        "name": val.name,
                        "slug": val.slug,
                        "archive": val.archive,
                        "rules": val.rules,
                    }
                    for val in variable.variablevalues_set.all()
                ]

                variables_data.append(
                    {
                        "id": variable.id,
                        "name": variable.name,
                        "slug": variable.slug,
                        "scope": variable.scope,
                        "all_cats": (variable.cat is None),
                        "archive": variable.archive,
                        "values": values_data,
                    }
                )

            levels_data.append(
                {
                    "id": level.id,
                    "name": level.name,
                    "slug": level.slug,
                    "url": level.url,
                    "rules": level.rules,
                    "variables": variables_data,
                }
            )

        return 200, levels_data

    except Exception as e:
        return 500, ErrorResponse(
            error="Failed to retrieve game levels",
            details={"exception": str(e)},
        )
