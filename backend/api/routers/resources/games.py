from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Games

from api.docs.games import GAMES_ALL, GAMES_DELETE, GAMES_GET, GAMES_POST, GAMES_PUT
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.games import GameCreateSchema, GameSchema, GameUpdateSchema

router = Router()


def game_embeds(
    queryset,
    embeds: str | None,
):
    """Add prefetches to a queryset based on embed parameter."""
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
    auth=public_auth,
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

    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
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

    **Supported Parameters:**
    - `limit` (Optional[int]): Results per page (default 50, max 100).
    - `offset` (Optional[int]): Results to skip (default 0).
    - `embed` (Optional[list]): Comma-separated list of resources to embed,

    **Supported Embeds:**
    - `categories`: Include metadata related to the game's categories.
    - `levels`: Include metadata related to the game's levels.
    - `platforms`: Include metadata related to the game's available platforms.
    
    **Examples:**
    - `/games/all` - Get all games.
    - `/games/all?limit=20` - Get first 20 games.
    - `/games/all?embed=categories,platforms` - Get games with categories and platforms.
    """,
    auth=public_auth,
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
    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
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

        # Simple model validate on the game date received before putting it into
        # an array that is then sent back to the client.
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

    **Request Body:**
    - `name` (str): Game name.
    - `slug` (str): URL-friendly game abbreviation.
    - `twitch` (Optional[str]): Game name as it appears on Twitch.
    - `release` (date): Game release date (ISO format).
    - `boxart` (str): URL to game box art/cover image.
    - `defaulttime` (str): Default timing method for full-game runs.
    - `idefaulttime` (str): Default timing method for individual level runs.
    - `pointsmax` (int): Maximum points for world record full-game runs.
    - `ipointsmax` (int): Maximum points for world record individual level runs.
    """,
    auth=moderator_auth,
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
                error="Game Already Exists",
                details={
                    "exception": "Either the name of the game or its slug already exists."
                },
                code=400,
            )

        game = Games.objects.create(**game_data.model_dump())

        return GameSchema.model_validate(game)
    except Exception as e:
        return ErrorResponse(
            error="Game Creation Failed",
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

    **Request Body:**
    - `name` (Optional[str]): Game name.
    - `slug` (Optional[str]): URL-friendly game abbreviation.
    - `twitch` (Optional[str]): Game name as it appears on Twitch.
    - `release` (Optiional[date]): Game release date (ISO format).
    - `boxart` (Optional[str]): URL to game box art/cover image.
    - `defaulttime` (Optional[str]): Default timing method for full-game runs.
    - `idefaulttime` (Optional[str]): Default timing method for individual level runs.
    - `pointsmax` (Optional[int]): Maximum points for world record full-game runs.
    - `ipointsmax` (Optional[int]): Maximum points for world record individual level runs.
    """,
    auth=moderator_auth,
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

    **Supported Parameters:**
    - id (str): Unique ID or slug of the specified game
    """,
    auth=admin_auth,
    openapi_extra=GAMES_DELETE,
)
def delete_game(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        game = Games.objects.filter(Q(id__iexact=id) | Q(slug__iexact=id)).first()
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
