from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import CountryCodes, Players, Runs

from api.docs.players import PLAYERS_DELETE, PLAYERS_GET, PLAYERS_POST, PLAYERS_PUT
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.players import PlayerCreateSchema, PlayerSchema, PlayerUpdateSchema

router = Router()


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

    # Embeds the 25 most recent runs to the player query, if runs is an embed.
    if "runs" in embed_fields:
        recent_runs = (
            Runs.objects.filter(player=player)
            .select_related("game", "category", "level")
            .order_by("-v_date")[:25]
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

    **Supported Parameters:**
    - `id` (str): Unique ID of the player being queried.
    - `embed` (Optional[list]): Comma-separated list of resources to embed.

    **Supported Embeds:**
    - `country`: Includes the metadata of the country associated with the player, if any.
    - `awards`: Include the metadata of the awards the player has collected, if any.
    - `runs`: Includes the metadata for all runs associated with the player.

    **Examples:**
    - `/players/v8lponvj` - Get player by ID.
    - `/players/v8lponvj?embed=country` - Get player with country info.
    - `/players/v8lponvj?embed=country,awards,runs` - Get player with all embeds.
    """,
    auth=public_auth,
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

    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
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


@router.post(
    "/",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Create Player",
    description="""
    Creates a brand new player.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Request Body:**
    - id (str): Unique ID (usually based on SRC) of the player.
    - name (str): Player's name on Speedrun.com.
    - nickname (Optional[str]): Custom nickname override (displayed instead of name).
    - url (str): Speedrun.com profile URL.
    - pfp (Optional[str]): Profile picture URL.
    - pronouns (Optional[str]): Player's pronouns.
    - twitch (Optional[str]): Twitch channel URL.
    - youtube (Optional[str]): YouTube channel URL.
    - twitter (Optional[str]): Twitter profile URL.
    - bluesky (Optional[str]): Bluesky profile URL.
    - ex_stream (bool): Whether the player is marked to be excluded from streams.
    """,
    auth=moderator_auth,
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

    **Supported Parameters:**
    - `id` (str): Unique ID of the player being updated.

    **Request Body:**
    - name (Optional[str]): Player's name on Speedrun.com.
    - nickname (Optional[str]): Custom nickname override (displayed instead of name).
    - url (Optional[str]): Speedrun.com profile URL.
    - pfp (Optional[str]): Profile picture URL.
    - pronouns (Optional[str]): Player's pronouns.
    - twitch (Optional[str]): Twitch channel URL.
    - youtube (Optional[str]): YouTube channel URL.
    - twitter (Optional[str]): Twitter profile URL.
    - bluesky (Optional[str]): Bluesky profile URL.
    - ex_stream (Optional[bool]): Whether the player is marked to be excluded from streams.
    """,
    auth=moderator_auth,
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

    **Supported Parameters:**
    - `id` (str): Unique ID of the player being deleted.
    """,
    auth=admin_auth,
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
