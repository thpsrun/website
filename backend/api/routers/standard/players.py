from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import CountryCodes, Players, Runs

from api.auth.api_key import api_key_required, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.players import (
    PlayerCreateSchema,
    PlayerSchema,
    PlayerUpdateSchema,
)

players_router = Router(tags=["Players"])


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
        # Limit runs for performance - get recent runs only
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


@players_router.get(
    "/{id}",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Get Player by ID",
    description="""
    Retrieve a single player by their ID.

    **Supported Embeds:**
    - `country`: Include country information
    - `awards`: Include player's earned awards
    - `runs`: Include recent runs (limited to 20 for performance)

    **Examples:**
    - `/players/v8lponvj` - Basic player data
    - `/players/v8lponvj?embed=country,awards` - Include country and awards
    - `/players/v8lponvj?embed=runs` - Include recent runs
    """,
    auth=read_only_auth,
)
def get_player(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
) -> Union[PlayerSchema, ErrorResponse]:
    """Get a single player by ID."""
    if len(id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    # Parse embeds
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
            return ErrorResponse(error="Player ID does not exist", code=404)

        player_data = PlayerSchema.model_validate(player)

        if embed_fields:
            embed_data = apply_player_embeds(player, embed_fields)
            for field, data in embed_data.items():
                setattr(player_data, field, data)

        return player_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve player", details={"exception": str(e)}, code=500
        )


@players_router.get(
    "/all",
    response=Union[List[PlayerSchema], ErrorResponse],
    summary="Get All Players",
    description="""
    Retrieve all players with optional filtering and embeds.

    **Query Parameters:**
    - `country`: Filter by country code ID
    - `search`: Search by player name or nickname
    - `embed`: Include related data
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Performance Note:**
    The `runs` embed is limited to recent runs for performance reasons.
    """,
    auth=read_only_auth,
)
def get_all_players(
    request: HttpRequest,
    country: Optional[str] = Query(None, description="Filter by country code"),
    search: Optional[str] = Query(None, description="Search by name"),
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Union[List[PlayerSchema], ErrorResponse]:
    """Get all players with optional filtering."""
    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("players", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}", code=400
            )

    try:
        queryset = Players.objects.all().order_by("name")

        if country:
            queryset = queryset.filter(countrycode__id=country)
        if search:
            # Search in both name and nickname fields
            from django.db.models import Q

            queryset = queryset.filter(
                Q(name__icontains=search) | Q(nickname__icontains=search)
            )

        players = queryset[offset : offset + limit]

        player_schemas = []
        for player in players:
            player_data = PlayerSchema.model_validate(player)

            if embed_fields:
                embed_data = apply_player_embeds(player, embed_fields)
                for field, data in embed_data.items():
                    setattr(player_data, field, data)

            player_schemas.append(player_data)

        return player_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve players", details={"exception": str(e)}, code=500
        )


@players_router.post(
    "/",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Create Player",
    auth=api_key_required,
)
def create_player(
    request: HttpRequest,
    player_data: PlayerCreateSchema,
) -> Union[PlayerSchema, ErrorResponse]:
    """Create a new player."""
    try:
        # Handle country code
        country = None
        if player_data.country_id:
            country = CountryCodes.objects.filter(id=player_data.country_id).first()
            if not country:
                return ErrorResponse(error="Country code does not exist", code=400)

        # Create player
        create_data = player_data.dict(exclude={"country_id"})
        player = Players.objects.create(countrycode=country, **create_data)

        return PlayerSchema.model_validate(player)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create player", details={"exception": str(e)}, code=500
        )


@players_router.put(
    "/{id}",
    response=Union[PlayerSchema, ErrorResponse],
    summary="Update Player",
    auth=api_key_required,
)
def update_player(
    request: HttpRequest,
    id: str,
    player_data: PlayerUpdateSchema,
) -> Union[PlayerSchema, ErrorResponse]:
    """Update an existing player."""
    try:
        player = Players.objects.filter(id__iexact=id).first()
        if not player:
            return ErrorResponse(error="Player does not exist", code=404)

        update_data = player_data.dict(exclude_unset=True)

        # Handle country code update
        if "country_id" in update_data:
            if update_data["country_id"]:
                country = CountryCodes.objects.filter(
                    id=update_data["country_id"]
                ).first()
                if not country:
                    return ErrorResponse(error="Country code does not exist", code=400)
                player.countrycode = country
            else:
                player.countrycode = None
            del update_data["country_id"]

        # Update other fields
        for field, value in update_data.items():
            setattr(player, field, value)

        player.save()
        return PlayerSchema.model_validate(player)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update player", details={"exception": str(e)}, code=500
        )


@players_router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Player",
    auth=api_key_required,
)
def delete_player(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    """Delete a player."""
    try:
        player = Players.objects.filter(id__iexact=id).first()
        if not player:
            return ErrorResponse(error="Player does not exist", code=404)

        name = player.nickname if player.nickname else player.name
        player.delete()
        return {"message": f"Player '{name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete player", details={"exception": str(e)}, code=500
        )
