from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from django.db.models import Case, IntegerField, Prefetch, Q, QuerySet, Value, When
from django.db.models.functions import TruncDate
from django.http import HttpRequest
from ninja import Path, Query, Router
from srl.models import Categories, Games, Levels, Runs, Variables

from api.auth import read_only_auth
from api.permissions import public_auth
from api.schemas.base import ErrorResponse

if TYPE_CHECKING:
    from srl.models import RunPlayers

router = Router()

# START OPENAPI DOCUMENTATION #
MAIN_PAGE_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "latest_wrs": [
                            {
                                "id": "y8dwozoj",
                                "game": {
                                    "name": "Tony Hawk's Pro Skater 4",
                                    "slug": "thps4",
                                },
                                "category": {"name": "Any%"},
                                "subcategory": "Normal, PC",
                                "players": [
                                    {"name": "ThePackle", "country": "United States"}
                                ],
                                "time": "12:34.567",
                                "date": "2025-08-15T10:30:00Z",
                                "video": "https://youtube.com/watch?v=example",
                                "url": "https://speedrun.com/thps4/run/y8dwozoj",
                            }
                        ],
                        "latest_pbs": [
                            {
                                "id": "z9fxpakl",
                                "game": {
                                    "name": "Tony Hawk's Pro Skater 3",
                                    "slug": "thps3",
                                },
                                "category": {"name": "100%"},
                                "subcategory": "Normal, PS2",
                                "players": [
                                    {"name": "SpeedRunner123", "country": "Canada"}
                                ],
                                "time": "25:43.123",
                                "place": 2,
                                "date": "2025-01-14T15:20:00Z",
                                "video": "https://youtube.com/watch?v=example2",
                                "url": "https://speedrun.com/thps3/run/z9fxpakl",
                            }
                        ],
                        "records": [
                            {
                                "game": {
                                    "name": "Tony Hawk's Pro Skater 4",
                                    "slug": "thps4",
                                    "release": "2002-10-23",
                                },
                                "subcategory": "Normal, PC",
                                "time": "12:34.567",
                                "players": [
                                    {
                                        "player": {
                                            "name": "ThePackle",
                                            "country": "United States",
                                        },
                                        "url": "https://speedrun.com/thps4/run/y8dwozoj",
                                        "date": "2025-08-15",
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid data types requested or missing data parameter."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "data",
            "in": "query",
            "required": True,
            "example": "latest-wrs,latest-pbs,records",
            "schema": {"type": "string"},
            "description": "Comma-separated data types: latest-wrs, latest-pbs, records",
        },
    ],
}

GAME_CATEGORIES_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "rklge08d",
                            "name": "Any%",
                            "slug": "any",
                            "type": "per-game",
                            "url": "https://speedrun.com/thps4/full_game#Any",
                            "rules": "Rulez.",
                            "appear_on_main": True,
                            "hidden": False,
                            "variables": [
                                {
                                    "id": "5lygdn8q",
                                    "name": "Platform",
                                    "slug": "platform",
                                    "scope": "full-game",
                                    "all_cats": True,
                                    "hidden": False,
                                    "values": [
                                        {
                                            "value": "pc",
                                            "name": "PC",
                                            "slug": "pc",
                                            "hidden": False,
                                            "rules": "",
                                        },
                                        {
                                            "value": "ps2",
                                            "name": "PlayStation 2",
                                            "slug": "ps2",
                                            "hidden": False,
                                            "rules": "",
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "id": "xd1m508k",
                            "name": "100%",
                            "slug": "100",
                            "type": "per-game",
                            "url": "https://speedrun.com/thps4/full_game#100",
                            "rules": "",
                            "appear_on_main": True,
                            "hidden": False,
                            "variables": [
                                {
                                    "id": "5lygdn8q",
                                    "name": "Platform",
                                    "slug": "platform",
                                    "scope": "full-game",
                                    "all_cats": True,
                                    "hidden": False,
                                    "values": [
                                        {
                                            "value": "pc",
                                            "name": "PC",
                                            "slug": "pc",
                                            "hidden": False,
                                            "rules": "",
                                        }
                                    ],
                                }
                            ],
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Game could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "path",
            "required": True,
            "example": "thps4",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Game ID or slug",
        },
    ],
}

GAME_LEVELS_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "592pxj8d",
                            "name": "Alcatraz",
                            "slug": "alcatraz",
                            "url": "https://speedrun.com/thps4/individual_levels#Alcatraz",
                            "rules": "Rulez.",
                            "variables": [
                                {
                                    "id": "9k2xfl7m",
                                    "name": "Difficulty",
                                    "slug": "difficulty",
                                    "scope": "single-level",
                                    "all_cats": False,
                                    "hidden": False,
                                    "values": [
                                        {
                                            "value": "normal",
                                            "name": "Normal",
                                            "slug": "normal",
                                            "hidden": False,
                                            "rules": "",
                                        },
                                        {
                                            "value": "sick",
                                            "name": "Sick",
                                            "slug": "sick",
                                            "hidden": False,
                                            "rules": "",
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "id": "29vjx18k",
                            "name": "Kona",
                            "slug": "kona",
                            "url": "https://speedrun.com/thps4/individual_levels#Kona",
                            "rules": "Rulez.",
                            "variables": [
                                {
                                    "id": "9k2xfl7m",
                                    "name": "Difficulty",
                                    "slug": "difficulty",
                                    "scope": "single-level",
                                    "all_cats": False,
                                    "hidden": False,
                                    "values": [
                                        {
                                            "value": "normal",
                                            "name": "Normal",
                                            "slug": "normal",
                                            "hidden": False,
                                            "rules": "",
                                        }
                                    ],
                                }
                            ],
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Game could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "path",
            "required": True,
            "example": "thps4",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Game ID or slug",
        },
    ],
}
# END OPENAPI DOCUMENTATION #


@router.get(
    "/main",
    response=Union[Dict[str, Any], ErrorResponse],
    summary="Get Main Page Data",
    description="""
    Get aggregated data for the website main page including latest world records,
    personal bests, and current records for featured categories.

    **Supported Data Types:**
    - `latest-wrs`: Latest 5 world records
    - `latest-pbs`: Latest 5 personal bests (excluding WRs)
    - `records`: Current WRs for featured categories

    **Supported Parameters:**
    - `data`: Comma-separated list of data types to include (required)

    **Examples:**
    - `/website/main?data=latest-wrs,latest-pbs` - Recent activity
    - `/website/main?data=records` - Current world records
    - `/website/main?data=latest-wrs,latest-pbs,records` - All data

    **Note:** This is an aggregation endpoint optimized for the React frontend homepage.
    """,
    auth=public_auth,
    openapi_extra=MAIN_PAGE_GET,
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
            wrs: QuerySet[Runs] = (
                Runs.objects.exclude(vid_status__in=["new", "rejected"])
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(place=1, obsolete=False, v_date__isnull=False)
                .order_by("-v_date")[:5]
            )

            response_data["latest_wrs"] = []
            for run in wrs:
                run_players: "QuerySet[RunPlayers]" = run.run_players.select_related(
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
            pbs: QuerySet[Runs] = (
                Runs.objects.exclude(vid_status__in=["new", "rejected"])
                .select_related("game", "category")
                .prefetch_related("run_players__player__countrycode")
                .filter(place__gt=1, obsolete=False, v_date__isnull=False)
                .order_by("-v_date")[:5]
            )

            response_data["latest_pbs"] = []
            for run in pbs:
                run_players: "QuerySet[RunPlayers]" = run.run_players.select_related(
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
                        run_players: "QuerySet[RunPlayers]" = (
                            run.run_players.select_related(
                                "player__countrycode"
                            ).order_by("order")
                        )

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


@router.get(
    "/game/{game_id}/categories",
    response=Union[List[Dict[str, Any]], ErrorResponse],
    summary="Get Game Categories with Variables",
    description="""
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
    """,
    auth=read_only_auth,
    openapi_extra=GAME_CATEGORIES_GET,
)
def get_game_categories(
    request: HttpRequest,
    game_id: str = Path(
        ...,
        description="Game ID or slug",
    ),
) -> Union[List[Dict[str, Any]], ErrorResponse]:
    """Get categories for a game with variables."""
    if len(game_id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return ErrorResponse(
                error="Game not found",
                details=None,
                code=404,
            )

        # Get categories with custom ordering (same as DRF version)
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
                        "hidden": val.archive,
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
                        "hidden": variable.archive,
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
                    "hidden": category.hidden,
                    "variables": variables_data,
                }
            )

        return categories_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve game categories",
            details={"exception": str(e)},
            code=500,
        )


@router.get(
    "/game/{game_id}/levels",
    response=Union[List[Dict[str, Any]], ErrorResponse],
    summary="Get Game Levels with Variables",
    description="""
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
    """,
    auth=read_only_auth,
    openapi_extra=GAME_LEVELS_GET,
)
def get_game_levels(
    request: HttpRequest, game_id: str = Path(..., description="Game ID or slug")
) -> Union[List[Dict[str, Any]], ErrorResponse]:
    """Get levels for a game with variables (converted from Web_Levels.py)."""
    if len(game_id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return ErrorResponse(
                error="Game not found",
                details=None,
                code=404,
            )

        # Import the ordering function from the existing system
        from api.ordering import get_ordered_level_names

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
                        "hidden": val.archive,
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
                        "hidden": variable.archive,
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

        return levels_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve game levels",
            details={"exception": str(e)},
            code=500,
        )
