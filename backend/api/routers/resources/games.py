from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Games

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.games import GameCreateSchema, GameSchema, GameUpdateSchema

router = Router()

# START OPENAPI DOCUMENTATION #
GAMES_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
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
                    }
                }
            },
        },
        404: {"description": "Game does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "thps4",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Game ID or slug to retrieve",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "categories,levels",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: categories, levels, platforms",
        },
    ],
}

GAMES_POST = {
    "responses": {
        201: {
            "description": "Game created successfully!",
            "content": {
                "application/json": {
                    "example": {
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
                    }
                }
            },
        },
        400: {"description": "Invalid request data or game with slug already exists."},
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
                    "required": ["name", "slug"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Tony Hawk's Pro Skater 4",
                            "description": "GAME NAME",
                        },
                        "slug": {
                            "type": "string",
                            "example": "thps4",
                            "description": "GAME URL SLUG",
                        },
                        "release": {
                            "type": "string",
                            "format": "date",
                            "example": "2002-10-23",
                            "description": "GAME RELEASE DATE",
                        },
                        "boxart": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://example.com/boxart.jpg",
                            "description": "GAME BOXART URL",
                        },
                        "twitch": {
                            "type": "string",
                            "example": "Tony Hawk's Pro Skater 4",
                            "description": "TWITCH GAME NAME",
                        },
                        "defaulttime": {
                            "type": "string",
                            "enum": ["realtime", "realtime_noloads", "ingame"],
                            "example": "realtime",
                            "description": "DEFAULT TIMING METHOD",
                        },
                        "idefaulttime": {
                            "type": "string",
                            "enum": ["realtime", "realtime_noloads", "ingame"],
                            "example": "realtime",
                            "description": "DEFAULT IL TIMING METHOD",
                        },
                    },
                },
                "example": {
                    "name": "Tony Hawk's Pro Skater 4",
                    "slug": "thps4",
                    "release": "2002-10-23",
                    "boxart": "https://example.com/boxart.jpg",
                    "twitch": "Tony Hawk's Pro Skater 4",
                    "defaulttime": "realtime",
                    "idefaulttime": "realtime",
                },
            }
        },
    },
}

GAMES_PUT = {
    "responses": {
        200: {
            "description": "Game updated successfully!",
            "content": {
                "application/json": {
                    "example": {
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
                    }
                }
            },
        },
        400: {"description": "Invalid request data."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Game does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "thps4",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Game ID or slug to update",
        },
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Tony Hawk's Pro Skater 4",
                            "description": "UPDATED GAME NAME",
                        },
                        "slug": {
                            "type": "string",
                            "example": "thps4",
                            "description": "UPDATED GAME SLUG",
                        },
                        "release": {
                            "type": "string",
                            "format": "date",
                            "example": "2002-10-23",
                            "description": "UPDATED RELEASE DATE",
                        },
                        "boxart": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://example.com/boxart.jpg",
                            "description": "UPDATED BOXART URL",
                        },
                        "twitch": {
                            "type": "string",
                            "example": "Tony Hawk's Pro Skater 4",
                            "description": "UPDATED TWITCH NAME",
                        },
                        "defaulttime": {
                            "type": "string",
                            "enum": ["realtime", "realtime_noloads", "ingame"],
                            "example": "realtime",
                            "description": "UPDATED DEFAULT TIMING",
                        },
                        "idefaulttime": {
                            "type": "string",
                            "enum": ["realtime", "realtime_noloads", "ingame"],
                            "example": "realtime",
                            "description": "UPDATED IL DEFAULT TIMING",
                        },
                    },
                },
                "example": {
                    "name": "Tony Hawk's Pro Skater 4 Updated",
                    "boxart": "https://example.com/new-boxart.jpg",
                },
            }
        },
    },
}

GAMES_DELETE = {
    "responses": {
        200: {
            "description": "Game deleted successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Game 'Tony Hawk's Pro Skater 4' deleted successfully"
                    }
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions (admin required)."},
        404: {"description": "Game does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "thps4",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Game ID or slug to delete",
        },
    ],
}

GAMES_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
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
                        {
                            "id": "k6qw5o9p",
                            "name": "Tony Hawk's Pro Skater 3",
                            "slug": "thps3",
                            "release": "2001-10-28",
                            "boxart": "https://example.com/thps3-boxart.jpg",
                            "twitch": "Tony Hawk's Pro Skater 3",
                            "defaulttime": "realtime",
                            "idefaulttime": "realtime",
                            "pointsmax": 1000,
                            "ipointsmax": 100,
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
            "name": "embed",
            "in": "query",
            "example": "categories,levels",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: categories, levels, platforms",
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


def game_embeds(
    queryset,
    embeds: str | None,
):
    """Add prefetches to a queryset based on embed parameter.
    Valid embeds: categories, levels, platforms.
    """
    if not embeds:
        return queryset

    embed_list = [e.strip() for e in embeds.split(",")]

    if "categories" in embed_list:
        queryset = queryset.prefetch_related("categories_set")
    if "levels" in embed_list:
        queryset = queryset.prefetch_related("levels_set")
    if "platforms" in embed_list:
        queryset = queryset.prefetch_related("platforms")

    return queryset


@router.get(
    "/{id}",
    response=GameSchema,
    summary="Get Game by ID",
    description="""
    Retrieves a single game by its ID or its slug, including optional embedding.

    **Supported Embeds:**
    - `categories`: Include metadata related to the game's categories
    - `levels`: Include metadata related to the game's levels
    - `platforms`: Include metadata related to the game's available platforms

    **Examples:**
    - `/games/thps4` - Get game by slug
    - `/games/n2680o1p` - Get game by ID
    - `/games/thps4?embed=categories,levels` - Get game with categories and levels
    """,
    auth=read_only_auth,
    openapi_extra=GAMES_GET,
)
def get_game(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[GameSchema, ErrorResponse]:
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("games", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["categories", "levels", "platforms"]},
                code=400,
            )

    try:
        queryset = Games.objects.all()
        queryset = game_embeds(queryset, embed)

        game = queryset.filter(Q(id__iexact=id) | Q(slug__iexact=id)).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=404,
            )

        return GameSchema.model_validate(game)
    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve game",
            details={"exception": str(e)},
            code=500,
        )


@router.get(
    "/all",
    response=List[GameSchema],
    summary="Get All Games",
    description="""
    Retrieves all games within the `Games` object, including optional embedding and pagination.

    **Supported Embeds:**
    - `categories`: Include metadata related to the game's categories
    - `levels`: Include metadata related to the game's levels
    - `platforms`: Include metadata related to the game's available platforms

    **Supported Parameters:**
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/games/all` - Get all games
    - `/games/all?limit=20` - Get first 20 games
    - `/games/all?embed=categories,platforms` - Get games with categories and platforms
    """,
    auth=read_only_auth,
    openapi_extra=GAMES_ALL,
)
def get_all_games(
    request: HttpRequest,
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
) -> Union[List[GameSchema], ErrorResponse]:
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("games", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["categories", "levels", "platforms"]},
                code=400,
            )

    try:
        queryset = Games.objects.all().order_by("release")
        queryset = game_embeds(queryset, embed)
        games = queryset[offset : offset + limit]

        game_schemas = []
        for game in games:
            game_data = GameSchema.model_validate(game)
            game_schemas.append(game_data)

        return game_schemas
    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve games",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "",
    response=Union[GameSchema, ErrorResponse],
    summary="Create Game",
    description="""
    Creates a brand new game.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=GAMES_POST,
)
def create_game(
    request: HttpRequest,
    game_data: GameCreateSchema,
) -> Union[GameSchema, ErrorResponse]:
    try:
        game_check = Games.objects.filter(
            Q(name__iexact=game_data.name) | Q(slug__iexact=game_data.slug)
        ).first()
        if game_check:
            return ErrorResponse(
                error="Game already exists",
                details={
                    "exception": "Either the name of the game or its slug already exists."
                },
                code=400,
            )

        game = Games.objects.create(**game_data.model_dump())

        return GameSchema.model_validate(game)
    except Exception as e:
        return ErrorResponse(
            error="Failed to create game",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[GameSchema, ErrorResponse],
    summary="Update Game",
    description="""
    Updates the game based on its unique ID or slug.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=GAMES_PUT,
)
def update_game(
    request: HttpRequest,
    id: str,
    game_data: GameUpdateSchema,
) -> Union[GameSchema, ErrorResponse]:
    try:
        game = Games.objects.filter(Q(id__iexact=id) | Q(slug__iexact=id)).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=404,
            )

        for attr, value in game_data.model_dump(exclude_unset=True).items():
            setattr(game, attr, value)

        game.save()
        return GameSchema.model_validate(game)
    except Exception as e:
        return ErrorResponse(
            error="Failed to update game",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Game",
    description="""
    Deletes the selected game.

    **REQUIRES ADMIN ACCESS.**
    """,
    auth=api_admin_check,
    openapi_extra=GAMES_DELETE,
)
def delete_game(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        game = Games.objects.filter(Q(id__iexact=id) | Q(slug_iexact=id)).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=404,
            )

        name = game.name
        game.delete()
        return {"message": f"Game '{name}' deleted successfully"}
    except Exception as e:
        return ErrorResponse(
            error="Failed to delete game",
            details={"exception": str(e)},
            code=500,
        )
