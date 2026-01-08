from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import (
    Categories,
    Games,
    Levels,
    Players,
    RunPlayers,
    Runs,
    RunVariableValues,
    Variables,
    VariableValues,
)

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.runs import RunCreateSchema, RunSchema, RunUpdateSchema

router = Router()

# START OPENAPI DOCUMENTATION #
RUNS_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "fsdfsdfsdfs",
                        "time": "12:34.567",
                        "place": 1,
                        "runtype": "main",
                        "subcategory": "Normal, PC",
                        "video": "https://youtube.com/watch?v=example",
                        "url": "https://speedrun.com/thps4/run/fsdfsdfsdfs",
                        "date": "2025-08-15",
                        "v_date": "2025-08-15T10:30:00Z",
                        "vid_status": "verified",
                        "obsolete": False,
                        "game": {
                            "id": "n2680o1p",
                            "name": "Tony Hawk's Pro Skater 4",
                            "slug": "thps4",
                            "release": "2002-10-23",
                            "boxart": "https://example.com/boxart.jpg",
                            "twitch": "Tony Hawk's Pro Skater 4",
                            "defaulttime": "realtime",
                            "idefaulttime": "realtime",
                            "pointsmax": 1000,
                            "ipointsmax": 100,
                        },
                        "category": {
                            "id": "rklge08d",
                            "name": "Any%",
                            "slug": "any",
                            "type": "per-game",
                            "url": "https://speedrun.com/thps4/full_game#Any",
                            "rules": "Rulez.",
                            "appear_on_main": True,
                            "hidden": False,
                        },
                        "players": [
                            {
                                "id": "v8lponvj",
                                "name": "ThePackle",
                                "url": "https://speedrun.com/user/ThePackle",
                                "country": "United States",
                                "pronouns": "he/him",
                                "twitch": "https://twitch.tv/thepackle",
                                "youtube": "https://youtube.com/thepackle",
                                "twitter": "https://twitter.com/thepackle",
                                "bluesky": "https://bsky.app/profile/@thepackle.bsky.social",
                                "order": 1,
                            }
                        ],
                        "variables": [
                            {
                                "variable": {
                                    "id": "5lygdn8q",
                                    "name": "NG+?",
                                    "slug": "ng-plus",
                                    "scope": "full-game",
                                },
                                "value": {"value": "pc", "name": "PC", "slug": "pc"},
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Run could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "y8dwozoj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Run ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,category,players,variables",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: game, category, level, players, variables",
        },
    ],
}

RUNS_POST = {
    "responses": {
        201: {
            "description": "Run created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "21q4tfg34f34",
                        "time": "12:34.567",
                        "place": 1,
                        "runtype": "main",
                        "subcategory": "Any% (Normal)",
                        "video": "https://youtube.com/watch?v=example",
                        "url": "https://speedrun.com/thps4/run/21q4tfg34f34",
                        "date": "2025-08-15",
                        "v_date": "2025-08-15T10:30:00Z",
                        "vid_status": "new",
                        "obsolete": False,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data, resource does not exist, or validation failed."
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["game_id", "time"],
                    "properties": {
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "GAME ID FOR THIS RUN",
                        },
                        "category_id": {
                            "type": "string",
                            "example": "rklge08d",
                            "description": "CATEGORY ID FOR THIS RUN",
                        },
                        "level_id": {
                            "type": "string",
                            "example": "592pxj8d",
                            "description": "LEVEL ID FOR IL RUNS",
                        },
                        "player_id": {
                            "type": "string",
                            "example": "v8lponvj",
                            "description": "PRIMARY PLAYER ID",
                        },
                        "player2_id": {
                            "type": "string",
                            "example": "x81m29qk",
                            "description": "SECOND PLAYER ID FOR CO-OP RUNS",
                        },
                        "time": {
                            "type": "string",
                            "example": "12:34.567",
                            "description": "RUN TIME",
                        },
                        "runtype": {
                            "type": "string",
                            "enum": ["main", "il"],
                            "example": "main",
                            "description": "RUN TYPE",
                        },
                        "subcategory": {
                            "type": "string",
                            "example": "Normal, PC",
                            "description": "RUN SUBCATEGORY TEXT",
                        },
                        "video": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://youtube.com/watch?v=example",
                            "description": "VIDEO URL",
                        },
                        "date": {
                            "type": "string",
                            "format": "date",
                            "example": "2025-08-15",
                            "description": "RUN DATE",
                        },
                        "variable_values": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "example": {"5lygdn8q": "pc"},
                            "description": "VARIABLE ID TO VALUE ID MAPPING",
                        },
                    },
                },
                "example": {
                    "game_id": "n2680o1p",
                    "category_id": "rklge08d",
                    "player_id": "v8lponvj",
                    "time": "12:34.567",
                    "runtype": "main",
                    "subcategory": "Normal, PC",
                    "video": "https://youtube.com/watch?v=example",
                    "date": "2025-08-15",
                    "variable_values": {"5lygdn8q": "pc"},
                },
            }
        },
    },
}

RUNS_PUT = {
    "responses": {
        200: {
            "description": "Run updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "21q4tfg34f34",
                        "time": "12:34.567",
                        "place": 1,
                        "runtype": "main",
                        "subcategory": "Any% (Normal)",
                        "video": "https://youtube.com/watch?v=example",
                        "url": "https://speedrun.com/thps4/run/21q4tfg34f34",
                        "date": "2025-08-15",
                        "v_date": "2025-08-15T10:30:00Z",
                        "vid_status": "new",
                        "obsolete": False,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data, game/category/level/player does not exist."
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Run does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "y8dwozoj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Run ID to update",
        },
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "UPDATED GAME ID",
                        },
                        "category_id": {
                            "type": "string",
                            "example": "rklge08d",
                            "description": "UPDATED CATEGORY ID",
                        },
                        "level_id": {
                            "type": "string",
                            "example": "592pxj8d",
                            "description": "UPDATED LEVEL ID",
                        },
                        "player_id": {
                            "type": "string",
                            "example": "v8lponvj",
                            "description": "UPDATED PRIMARY PLAYER ID",
                        },
                        "player2_id": {
                            "type": "string",
                            "example": "x81m29qk",
                            "description": "UPDATED SECOND PLAYER ID",
                        },
                        "time": {
                            "type": "string",
                            "example": "12:34.567",
                            "description": "UPDATED RUN TIME",
                        },
                        "runtype": {
                            "type": "string",
                            "enum": ["main", "il"],
                            "example": "main",
                            "description": "UPDATED RUN TYPE",
                        },
                        "subcategory": {
                            "type": "string",
                            "example": "Normal, PC",
                            "description": "UPDATED SUBCATEGORY",
                        },
                        "video": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://youtube.com/watch?v=example",
                            "description": "UPDATED VIDEO URL",
                        },
                        "date": {
                            "type": "string",
                            "format": "date",
                            "example": "2025-08-15",
                            "description": "UPDATED RUN DATE",
                        },
                        "vid_status": {
                            "type": "string",
                            "enum": ["new", "verified", "rejected"],
                            "example": "verified",
                            "description": "UPDATED VERIFICATION STATUS",
                        },
                        "variable_values": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "example": {"5lygdn8q": "pc"},
                            "description": "UPDATED VARIABLE VALUES",
                        },
                    },
                },
                "example": {
                    "time": "12:30.000",
                    "video": "https://youtube.com/watch?v=newvideo",
                    "vid_status": "verified",
                },
            }
        },
    },
}

RUNS_DELETE = {
    "responses": {
        200: {
            "description": "Run deleted successfully!",
            "content": {
                "application/json": {"example": {"message": "Run deleted successfully"}}
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Run does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "y8dwozoj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Run ID to delete",
        },
    ],
}

RUNS_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "y8dwozoj",
                            "time": "12:34.567",
                            "place": 1,
                            "runtype": "main",
                            "subcategory": "Any% (No Major Glitches)",
                            "video": "https://youtube.com/watch?v=example",
                            "url": "https://speedrun.com/thps4/run/y8dwozoj",
                            "date": "2025-08-15",
                            "v_date": "2025-08-15T10:30:00Z",
                            "vid_status": "verified",
                            "obsolete": False,
                        },
                        {
                            "id": "z9fxpakl",
                            "time": "13:45.123",
                            "place": 2,
                            "runtype": "main",
                            "subcategory": "Any% (No Major Glitches)",
                            "video": "https://youtube.com/watch?v=example2",
                            "url": "https://speedrun.com/thps4/run/z9fxpakl",
                            "date": "2025-01-14",
                            "v_date": "2025-01-14T15:20:00Z",
                            "vid_status": "verified",
                            "obsolete": False,
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "query",
            "example": "thps4",
            "schema": {"type": "string"},
            "description": "Filter by game",
        },
        {
            "name": "category_id",
            "in": "query",
            "example": "rklge08d",
            "schema": {"type": "string"},
            "description": "Filter by category",
        },
        {
            "name": "level_id",
            "in": "query",
            "example": "592pxj8d",
            "schema": {"type": "string"},
            "description": "Filter by level",
        },
        {
            "name": "player_id",
            "in": "query",
            "example": "v8lponvj",
            "schema": {"type": "string"},
            "description": "Filter by player",
        },
        {
            "name": "runtype",
            "in": "query",
            "example": "main",
            "schema": {"type": "string", "pattern": "^(main|il)$"},
            "description": "Filter by run type",
        },
        {
            "name": "place",
            "in": "query",
            "example": 1,
            "schema": {"type": "integer", "minimum": 1},
            "description": "Filter by place",
        },
        {
            "name": "status",
            "in": "query",
            "example": "verified",
            "schema": {"type": "string", "pattern": "^(verified|new|rejected)$"},
            "description": "Filter by status",
        },
        {
            "name": "search",
            "in": "query",
            "example": "normal",
            "schema": {"type": "string"},
            "description": "Search subcategory text",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,category,players",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds",
        },
        {
            "name": "limit",
            "in": "query",
            "example": 50,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100},
            "description": "Results per page (default 50, max 100)",
        },
        {
            "name": "offset",
            "in": "query",
            "example": 0,
            "schema": {"type": "integer", "minimum": 0},
            "description": "Results to skip (default 0)",
        },
    ],
}
# END OPENAPI DOCUMENTATION #


def apply_run_embeds(
    run: Runs,
    embed_fields: List[str],
) -> dict:
    """
    Apply requested embeds to a run instance.

    This is the most complex embed function due to all the relationships
    runs have with other models.
    """
    embeds = {}

    if "game" in embed_fields and run.game:
        embeds["game"] = {
            "id": run.game.id,
            "name": run.game.name,
            "slug": run.game.slug,
            "release": run.game.release.isoformat(),
            "boxart": run.game.boxart,
            "twitch": run.game.twitch,
            "defaulttime": run.game.defaulttime,
            "idefaulttime": run.game.idefaulttime,
            "pointsmax": run.game.pointsmax,
            "ipointsmax": run.game.ipointsmax,
        }

    if "category" in embed_fields and run.category:
        embeds["category"] = {
            "id": run.category.id,
            "name": run.category.name,
            "slug": run.category.slug,
            "type": run.category.type,
            "url": run.category.url,
            "rules": run.category.rules,
            "appear_on_main": run.category.appear_on_main,
            "hidden": run.category.archive,
        }

    if "level" in embed_fields and run.level:
        embeds["level"] = {
            "id": run.level.id,
            "name": run.level.name,
            "slug": run.level.slug,
            "url": run.level.url,
            "rules": run.level.rules,
        }

    if "player" in embed_fields or "player2" in embed_fields:
        run_players = run.players.select_related("player__countrycode").order_by(
            "order"
        )

        for rp in run_players:
            player_data = {
                "id": rp.player.id,
                "name": (
                    rp.player.nickname if rp.player.nickname else rp.player.name
                ),
                "url": rp.player.url,
                "country": (
                    rp.player.countrycode.name if rp.player.countrycode else None
                ),
                "pronouns": rp.player.pronouns,
                "twitch": rp.player.twitch,
                "youtube": rp.player.youtube,
                "twitter": rp.player.twitter,
                "bluesky": rp.player.bluesky,
            }

            if rp.order == 1 and "player" in embed_fields:
                embeds["player"] = player_data
            elif rp.order == 2 and "player2" in embed_fields:
                embeds["player2"] = player_data

    if "variables" in embed_fields:
        try:
            run_variables = RunVariableValues.objects.filter(run=run).select_related(
                "variable", "value"
            )

            variables_data = []
            for rv in run_variables:
                if rv.variable and rv.value:
                    variables_data.append(
                        {
                            "variable": {
                                "id": rv.variable.id,
                                "name": rv.variable.name,
                                "slug": rv.variable.slug,
                                "scope": rv.variable.scope,
                            },
                            "value": {
                                "value": rv.value.value,
                                "name": rv.value.name,
                                "slug": rv.value.slug,
                            },
                        }
                    )

            embeds["variables"] = variables_data
        except Exception:
            embeds["variables"] = []

    return embeds


@router.get(
    "/{id}",
    response=Union[RunSchema, ErrorResponse],
    summary="Get Run by ID",
    description="""
    Retrieve a single run by its ID with full details and optional embeds.

    **Supported Embeds:**
    - `game`: Include game information
    - `category`: Include category information
    - `level`: Include level information (for IL runs)
    - `player`: Include primary player details
    - `player2`: Include second player details (for co-op runs)
    - `variables`: Include variable selections (subcategories)

    **Examples:**
    - `/runs/y8dwozoj` - Basic run data
    - `/runs/y8dwozoj?embed=game,player` - Include game and player
    - `/runs/y8dwozoj?embed=player,player2,variables` - Co-op run with variables
    - `/runs/y8dwozoj?embed=game,category,level,player` - Full run details
    """,
    auth=read_only_auth,
    openapi_extra=RUNS_GET,
)
def get_run(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[RunSchema, ErrorResponse]:
    """Get a single run by ID."""
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("runs", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={
                    "valid_embeds": [
                        "game",
                        "category",
                        "level",
                        "player",
                        "player2",
                        "variables",
                    ]
                },
                code=400,
            )

    try:
        run = Runs.objects.filter(id__iexact=id).first()
        if not run:
            return ErrorResponse(
                error="Run ID does not exist",
                details=None,
                code=404,
            )

        run_data = RunSchema.model_validate(run)

        if embed_fields:
            embed_data = apply_run_embeds(run, embed_fields)
            for field, data in embed_data.items():
                setattr(run_data, field, data)

        return run_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve run", details={"exception": str(e)}, code=500
        )


@router.get(
    "/all",
    response=Union[List[RunSchema], ErrorResponse],
    summary="Get All Runs",
    description="""
    Retrieve runs with extensive filtering and search capabilities.

    **Query Parameters:**
    - `game_id`: Filter by specific game ID or slug
    - `category_id`: Filter by specific category ID
    - `level_id`: Filter by specific level ID (for IL runs)
    - `player_id`: Filter by specific player ID
    - `runtype`: Filter by run type (`main` or `il`)
    - `place`: Filter by leaderboard position
    - `status`: Filter by verification status (`verified`, `new`, or `rejected`)
    - `search`: Search in subcategory text
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/runs/all?game_id=thps4` - All runs for THPS4
    - `/runs/all?game_id=thps4&category_id=any&place=1` - THPS4 Any% world records
    - `/runs/all?player_id=v8lponvj&runtype=main` - Player's full-game runs
    - `/runs/all?search=normal&place=1&status=verified` - Verified WRs with "normal" in subcategory
    - `/runs/all?game_id=thps4&level_id=alcatraz&embed=player,game` - Alcatraz ILs with embeds
    """,
    auth=read_only_auth,
    openapi_extra=RUNS_ALL,
)
def get_all_runs(
    request: HttpRequest,
    game_id: Optional[str] = Query(
        None,
        description="Filter by game",
    ),
    category_id: Optional[str] = Query(
        None,
        description="Filter by category",
    ),
    level_id: Optional[str] = Query(
        None,
        description="Filter by level",
    ),
    player_id: Optional[str] = Query(
        None,
        description="Filter by player",
    ),
    runtype: Optional[str] = Query(
        None,
        description="Filter by type",
        pattern="^(main|il)$",
    ),
    place: Optional[int] = Query(
        None,
        description="Filter by place",
        ge=1,
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status",
        pattern="^(verified|new|rejected)$",
    ),
    search: Optional[str] = Query(
        None,
        description="Search subcategory text",
    ),
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of returned objects (default 50, less than 100)",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset from 0",
    ),
) -> Union[List[RunSchema], ErrorResponse]:
    """Get runs with comprehensive filtering."""
    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("runs", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    try:
        queryset = Runs.objects.all().order_by("-v_date", "place")

        if game_id:
            queryset = queryset.filter(Q(game__id=game_id) | Q(game__slug=game_id))
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        if level_id:
            queryset = queryset.filter(level__id=level_id)
        if player_id:
            queryset = queryset.filter(
                Q(player__id=player_id) | Q(player2__id=player_id)
            )
        if runtype:
            queryset = queryset.filter(runtype=runtype)
        if place:
            queryset = queryset.filter(place=place)
        if status:
            # Map status to internal field names
            status_mapping = {
                "verified": "verified",
                "new": "new",
                "rejected": "rejected",
            }
            if status in status_mapping:
                queryset = queryset.filter(vid_status=status_mapping[status])
        if search:
            queryset = queryset.filter(subcategory__icontains=search)

        # Apply pagination
        runs = queryset[offset : offset + limit]

        # Convert to schemas
        run_schemas = []
        for run in runs:
            run_data = RunSchema.model_validate(run)

            if embed_fields:
                embed_data = apply_run_embeds(run, embed_fields)
                for field, data in embed_data.items():
                    setattr(run_data, field, data)

            run_schemas.append(run_data)

        return run_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve runs",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "/",
    response=Union[RunSchema, ErrorResponse],
    summary="Create Run",
    description="""
    Create a new speedrun record with full validation.

    **Complex Validation:**
    - Game/category/level relationships must be valid
    - Players must exist if specified
    - Variable values must match variable constraints
    - Run type must match category type

    **Variable Values Format:**
    ```json
    {
        "variable_values": {
            "variable_id_1": "value_id_1",
            "variable_id_2": "value_id_2"
        }
    }
    ```

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=RUNS_POST,
)
def create_run(
    request: HttpRequest,
    run_data: RunCreateSchema,
) -> Union[RunSchema, ErrorResponse]:
    try:
        game = Games.objects.filter(id=run_data.game_id).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=400,
            )

        category = None
        if run_data.category_id:
            category = Categories.objects.filter(
                id=run_data.category_id, game=game
            ).first()
            if not category:
                return ErrorResponse(
                    error="Category does not exist for this game",
                    details=None,
                    code=400,
                )

        level = None
        if run_data.level_id:
            level = Levels.objects.filter(id=run_data.level_id, game=game).first()
            if not level:
                return ErrorResponse(
                    error="Level does not exist for this game",
                    details=None,
                    code=400,
                )

        players_list = []
        if run_data.player_ids:
            for player_id in run_data.player_ids:
                player = Players.objects.filter(id=player_id).first()
                if not player:
                    return ErrorResponse(
                        error=f"Player with ID '{player_id}' does not exist",
                        details=None,
                        code=400,
                    )
                players_list.append(player)

        if category and run_data.runtype == "main" and category.type != "per-game":
            return ErrorResponse(
                error="Main runs require per-game categories",
                details=None,
                code=400,
            )
        if (
            level
            and run_data.runtype == "il"
            and category
            and category.type != "per-level"
        ):
            return ErrorResponse(
                error="IL runs require per-level categories",
                details=None,
                code=400,
            )

        create_data = run_data.model_dump(
            exclude={
                "game_id",
                "category_id",
                "level_id",
                "player_ids",
                "variable_values",
            }
        )

        run = Runs.objects.create(
            game=game,
            category=category,
            level=level,
            **create_data,
        )

        for index, player in enumerate(players_list, start=1):
            RunPlayers.objects.create(run=run, player=player, order=index)

        if run_data.variable_values:
            try:
                for var_id, value_id in run_data.variable_values.items():
                    variable = Variables.objects.filter(id=var_id).first()
                    value = VariableValues.objects.filter(
                        value=value_id, var=variable
                    ).first()

                    if variable and value:
                        RunVariableValues.objects.create(
                            run=run, variable=variable, value=value
                        )
            except Exception:
                pass

        return RunSchema.model_validate(run)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create run",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[RunSchema, ErrorResponse],
    summary="Update Run",
    description="""
    Updates the run based on its unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=RUNS_PUT,
)
def update_run(
    request: HttpRequest,
    id: str,
    run_data: RunUpdateSchema,
) -> Union[RunSchema, ErrorResponse]:
    """Update an existing run."""
    try:
        run = Runs.objects.filter(id__iexact=id).first()
        if not run:
            return ErrorResponse(
                error="Run does not exist",
                details=None,
                code=404,
            )

        update_data = run_data.model_dump(exclude_unset=True)

        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(
                    error="Game does not exist",
                    details=None,
                    code=400,
                )
            run.game = game
            del update_data["game_id"]

        if "category_id" in update_data:
            if update_data["category_id"]:
                category = Categories.objects.filter(
                    id=update_data["category_id"], game=run.game
                ).first()
                if not category:
                    return ErrorResponse(
                        error="Category does not exist for this game",
                        details=None,
                        code=400,
                    )
                run.category = category
            else:
                run.category = None
            del update_data["category_id"]

        if "level_id" in update_data:
            if update_data["level_id"]:
                level = Levels.objects.filter(
                    id=update_data["level_id"], game=run.game
                ).first()
                if not level:
                    return ErrorResponse(
                        error="Level does not exist for this game",
                        details=None,
                        code=400,
                    )
                run.level = level
            else:
                run.level = None
            del update_data["level_id"]

        if "player_ids" in update_data:
            RunPlayers.objects.filter(run=run).delete()

            if update_data["player_ids"]:
                for index, player_id in enumerate(update_data["player_ids"], start=1):
                    player = Players.objects.filter(id=player_id).first()
                    if not player:
                        return ErrorResponse(
                            error=f"Player with ID '{player_id}' does not exist",
                            details=None,
                            code=400,
                        )
                    RunPlayers.objects.create(run=run, player=player, order=index)

            del update_data["player_ids"]

        if "variable_values" in update_data:
            try:
                RunVariableValues.objects.filter(run=run).delete()

                if update_data["variable_values"]:
                    for var_id, value_id in update_data["variable_values"].items():
                        variable = Variables.objects.filter(id=var_id).first()
                        value = VariableValues.objects.filter(
                            value=value_id, var=variable
                        ).first()

                        if variable and value:
                            RunVariableValues.objects.create(
                                run=run, variable=variable, value=value
                            )
            except Exception:
                pass
            del update_data["variable_values"]

        for field, value in update_data.items():
            setattr(run, field, value)

        run.save()
        return RunSchema.model_validate(run)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update run",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Run",
    description="""
    Deletes the selected run by its ID.

    **REQUIRES ADMIN ACCESS.**
    """,
    auth=api_admin_check,
    openapi_extra=RUNS_DELETE,
)
def delete_run(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        run = Runs.objects.filter(id__iexact=id).first()
        if not run:
            return ErrorResponse(
                error="Run does not exist",
                details=None,
                code=404,
            )

        game_name = run.game.name if run.game else "Unknown"
        run_players = run.players.all()
        player_names = (
            ", ".join([p.name for p in run_players])
            if run_players.exists()
            else "Anonymous"
        )

        run.delete()
        return {"message": f"Run by {player_names} in {game_name} deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete run",
            details={"exception": str(e)},
            code=500,
        )
