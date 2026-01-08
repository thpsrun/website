from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import CountryCodes, Players, Runs

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.players import PlayerCreateSchema, PlayerSchema, PlayerUpdateSchema

router = Router()

# START OPENAPI DOCUMENTATION #
PLAYERS_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "v8lponvj",
                        "name": "ThePackle",
                        "nickname": "ThePackle",
                        "url": "https://speedrun.com/user/ThePackle",
                        "pronouns": "he/him",
                        "twitch": "https://twitch.tv/thepackle",
                        "youtube": "https://youtube.com/thepackle",
                        "twitter": "https://twitter.com/thepackle",
                        "bluesky": "https://bsky.app/profile/@thepackle.bsky.social",
                        "country": {"id": "us", "name": "United States"},
                        "awards": [
                            {
                                "name": "thps.run Admin",
                                "description": "He's the admin!!",
                                "image": "https://example.com/award.png",
                            }
                        ],
                        "runs": [
                            {
                                "id": "y8dwozoj",
                                "game": "Tony Hawk's Pro Skater 4",
                                "category": "Any%",
                                "level": None,
                                "place": 1,
                                "time": "12:34.567",
                                "date": "2025-08-15T10:30:00Z",
                                "video": "https://youtube.com/watch?v=example",
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Player could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "v8lponvj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Player ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "country,awards,runs",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: country, awards, runs",
        },
    ],
}

PLAYERS_POST = {
    "responses": {
        201: {
            "description": "Player created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "v8lponvj",
                        "name": "ThePackle",
                        "nickname": "ThePackle",
                        "url": "https://speedrun.com/user/ThePackle",
                        "pronouns": "he/him",
                        "twitch": "https://twitch.tv/thepackle",
                        "youtube": "https://youtube.com/thepackle",
                        "twitter": "https://twitter.com/thepackle",
                        "bluesky": "https://bsky.app/profile/thepackle",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or country does not exist."},
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
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "ThePackle",
                            "description": "PLAYER NAME",
                        },
                        "nickname": {
                            "type": "string",
                            "example": "ThePackle",
                            "description": "PLAYER NICKNAME",
                        },
                        "country_id": {
                            "type": "string",
                            "example": "us",
                            "description": "COUNTRY CODE ID",
                        },
                        "pronouns": {
                            "type": "string",
                            "example": "he/him",
                            "description": "PLAYER PRONOUNS",
                        },
                        "twitch": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://twitch.tv/thepackle",
                            "description": "TWITCH URL",
                        },
                        "youtube": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://youtube.com/thepackle",
                            "description": "YOUTUBE URL",
                        },
                        "twitter": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://twitter.com/thepackle",
                            "description": "TWITTER URL",
                        },
                        "bluesky": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://bsky.app/profile/thepackle",
                            "description": "BLUESKY URL",
                        },
                    },
                },
                "example": {
                    "name": "ThePackle",
                    "nickname": "ThePackle",
                    "country_id": "us",
                    "pronouns": "he/him",
                    "twitch": "https://twitch.tv/thepackle",
                },
            }
        },
    },
}

PLAYERS_PUT = {
    "responses": {
        200: {
            "description": "Player updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "v8lponvj",
                        "name": "ThePackle",
                        "nickname": "ThePackle",
                        "url": "https://speedrun.com/user/ThePackle",
                        "pronouns": "he/him",
                        "twitch": "https://twitch.tv/thepackle",
                        "youtube": "https://youtube.com/thepackle",
                        "twitter": "https://twitter.com/thepackle",
                        "bluesky": "https://bsky.app/profile/@thepackle.bsky.social",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or country does not exist."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Player does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "v8lponvj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Player ID to update",
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
                            "example": "ThePackle",
                            "description": "UPDATED PLAYER NAME",
                        },
                        "nickname": {
                            "type": "string",
                            "example": "ThePackle",
                            "description": "UPDATED PLAYER NICKNAME",
                        },
                        "country_id": {
                            "type": "string",
                            "example": "us",
                            "description": "UPDATED COUNTRY CODE ID",
                        },
                        "pronouns": {
                            "type": "string",
                            "example": "he/him",
                            "description": "UPDATED PLAYER PRONOUNS",
                        },
                        "twitch": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://twitch.tv/thepackle",
                            "description": "UPDATED TWITCH URL",
                        },
                        "youtube": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://youtube.com/thepackle",
                            "description": "UPDATED YOUTUBE URL",
                        },
                        "twitter": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://twitter.com/thepackle",
                            "description": "UPDATED TWITTER URL",
                        },
                        "bluesky": {
                            "type": "string",
                            "format": "uri",
                            "example": "https://bsky.app/profile/thepackle",
                            "description": "UPDATED BLUESKY URL",
                        },
                    },
                },
                "example": {"nickname": "NewNickname", "pronouns": "they/them"},
            }
        },
    },
}

PLAYERS_DELETE = {
    "responses": {
        200: {
            "description": "Player deleted successfully!",
            "content": {
                "application/json": {
                    "example": {"message": "Player 'ThePackle' deleted successfully"}
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Player does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "v8lponvj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Player ID to delete",
        },
    ],
}

PLAYERS_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "v8lponvj",
                            "name": "ThePackle",
                            "nickname": "ThePackle",
                            "url": "https://speedrun.com/user/ThePackle",
                            "pronouns": "he/him",
                            "twitch": "https://twitch.tv/thepackle",
                            "youtube": "https://youtube.com/thepackle",
                            "twitter": "https://twitter.com/thepackle",
                            "bluesky": "https://bsky.app/profile/@thepackle.bsky.social",
                        },
                        {
                            "id": "x81m29qk",
                            "name": "SpeedRunner123",
                            "nickname": "SpeedRunner123",
                            "url": "https://speedrun.com/user/SpeedRunner123",
                            "pronouns": "they/them",
                            "twitch": "https://twitch.tv/speedrunner123",
                            "youtube": None,
                            "twitter": None,
                            "bluesky": None,
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
            "name": "country",
            "in": "query",
            "example": "us",
            "schema": {"type": "string"},
            "description": "Filter by country code",
        },
        {
            "name": "search",
            "in": "query",
            "example": "ThePackle",
            "schema": {"type": "string"},
            "description": "Search by name",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "country,awards",
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


def apply_player_embeds(
    player: Players,
    embed_fields: List[str],
) -> dict:
    """Apply requested embeds to a player instance."""
    embeds = {}

    if "country" in embed_fields:
        if player.countrycode:
            embeds["country"] = {
                "id": player.countrycode.id,
                "name": player.countrycode.name,
            }

    if "awards" in embed_fields:
        awards = player.awards.all().order_by("name")
        embeds["awards"] = [
            {
                "name": award.name,
                "description": award.description,
                "image": award.image.url if award.image else None,
            }
            for award in awards
        ]

    if "runs" in embed_fields:
        recent_runs = (
            Runs.objects.filter(player=player)
            .select_related("game", "category", "level")
            .order_by("-v_date")[:20]
        )

        embeds["runs"] = [
            {
                "id": run.id,
                "game": run.game.name if run.game else None,
                "category": run.category.name if run.category else None,
                "level": run.level.name if run.level else None,
                "place": run.place,
                "time": run.time,
                "date": run.v_date.isoformat() if run.v_date else None,
                "video": run.video,
            }
            for run in recent_runs
        ]

    return embeds


@router.get(
    "/{id}",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Get Player by ID",
    description="""
    Retrieve a single player by their ID, including optional embedding.

    **Supported Embeds:**
    - `country`: Includes the metadata of the country associated with the player, if any
    - `awards`: Include the metadata of the awards the player has collected, if any
    - `runs`: Includes the metadata for all runs associated with the player

    **Examples:**
    - `/players/v8lponvj` - Get player by ID
    - `/players/v8lponvj?embed=country` - Get player with country info
    - `/players/v8lponvj?embed=country,awards,runs` - Get player with all embeds
    """,
    auth=read_only_auth,
    openapi_extra=PLAYERS_GET,
)
def get_player(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[PlayerSchema, ErrorResponse]:
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("players", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["country", "awards", "runs"]},
                code=400,
            )

    try:
        player = Players.objects.filter(id__iexact=id).first()
        if not player:
            return ErrorResponse(
                error="Player ID does not exist",
                details=None,
                code=404,
            )

        player_data = PlayerSchema.model_validate(player)

        if embed_fields:
            embed_data = apply_player_embeds(player, embed_fields)
            for field, data in embed_data.items():
                setattr(player_data, field, data)

        return player_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve player",
            details={"exception": str(e)},
            code=500,
        )


@router.get(
    "/all",
    response=Union[List[PlayerSchema], ErrorResponse],
    summary="Get All Players",
    description="""
    Retrieves all players within the `Players` object based on queries, with optional embedding.

    **Note:** The `runs` embed will not raise an error if used, but will not return results on this endpoint.

    **Supported Embeds:**
    - `country`: Includes the metadata of the country associated with the player, if any
    - `awards`: Include the metadata of the awards the player has collected, if any

    **Supported Parameters:**
    - `country`: Filter by country code ID or slug
    - `player`: Filter based on a player's name, nickname, or slug
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/players/all` - Get all players
    - `/players/all?country=us` - Get all US players
    - `/players/all?player=thepackle` - Search for players with "thepackle" in name
    - `/players/all?country=us&embed=awards` - Get US players with their awards
    """,
    auth=read_only_auth,
    openapi_extra=PLAYERS_ALL,
)
def get_all_players(
    request: HttpRequest,
    country: Optional[str] = Query(
        None,
        description="Filter by country code",
    ),
    player: Optional[str] = Query(
        None,
        description="Filter by name, nickname, or slug",
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
) -> Union[List[PlayerSchema], ErrorResponse]:
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("players", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    try:
        queryset = Players.objects.all().order_by("name")

        if country:
            queryset = queryset.filter(countrycode__id=country)
        if player:
            queryset = queryset.filter(
                Q(name__icontains=player)
                | Q(nickname__icontains=player)
                | Q(slug__icontains=player)
            )

        players = queryset[offset : offset + limit]

        player_schemas = []
        for play in players:
            player_data = PlayerSchema.model_validate(play)

            if embed_fields:
                embed_data = apply_player_embeds(play, embed_fields)
                for field, data in embed_data.items():
                    setattr(player_data, field, data)

            player_schemas.append(player_data)

        return player_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve players",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "/",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Create Player",
    description="""
    Creates a brand new player.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=PLAYERS_POST,
)
def create_player(
    request: HttpRequest,
    player_data: PlayerCreateSchema,
) -> Union[PlayerSchema, ErrorResponse]:
    try:
        country = None
        if player_data.country_id:
            country = CountryCodes.objects.filter(id=player_data.country_id).first()
            if not country:
                return ErrorResponse(
                    error="Country code does not exist",
                    details=None,
                    code=400,
                )

        create_data = player_data.model_dump(exclude={"country_id"})
        player = Players.objects.create(countrycode=country, **create_data)

        return PlayerSchema.model_validate(player)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create player",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Update Player",
    description="""
    Updates the player based on their unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=PLAYERS_PUT,
)
def update_player(
    request: HttpRequest,
    id: str,
    player_data: PlayerUpdateSchema,
) -> Union[PlayerSchema, ErrorResponse]:
    try:
        player = Players.objects.filter(id__iexact=id).first()
        if not player:
            return ErrorResponse(
                error="Player does not exist",
                details=None,
                code=404,
            )

        update_data = player_data.model_dump(exclude_unset=True)

        if "country_id" in update_data:
            if update_data["country_id"]:
                country = CountryCodes.objects.filter(
                    id=update_data["country_id"]
                ).first()
                if not country:
                    return ErrorResponse(
                        error="Country code does not exist",
                        details=None,
                        code=400,
                    )
                player.countrycode = country
            else:
                player.countrycode = None
            del update_data["country_id"]

        for field, value in update_data.items():
            setattr(player, field, value)

        player.save()
        return PlayerSchema.model_validate(player)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update player",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Player",
    description="""
    Deletes the selected player based on its ID.

    **REQUIRES ADMIN ACCESS.**
    """,
    auth=api_admin_check,
    openapi_extra=PLAYERS_DELETE,
)
def delete_player(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        player = Players.objects.filter(id__iexact=id).first()
        if not player:
            return ErrorResponse(
                error="Player does not exist",
                details=None,
                code=404,
            )

        name = player.nickname if player.nickname else player.name
        player.delete()
        return {"message": f"Player '{name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete player",
            details={"exception": str(e)},
            code=500,
        )
