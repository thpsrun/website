from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Games, Levels, Variables, VariableValues

from api.auth.api_key import api_key_required, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.levels import LevelCreateSchema, LevelSchema, LevelUpdateSchema

levels_router = Router(tags=["Levels"])


def apply_level_embeds(
    level: Levels,
    embed_fields: List[str],
) -> dict:
    """Apply requested embeds to a level instance."""
    embeds = {}

    if "game" in embed_fields:
        if level.game:
            embeds["game"] = {
                "id": level.game.id,
                "name": level.game.name,
                "slug": level.game.slug,
                "release": level.game.release.isoformat(),
                "boxart": level.game.boxart,
                "twitch": level.game.twitch,
                "defaulttime": level.game.defaulttime,
                "idefaulttime": level.game.idefaulttime,
                "pointsmax": level.game.pointsmax,
                "ipointsmax": level.game.ipointsmax,
            }

    if "variables" in embed_fields or "values" in embed_fields:
        # Get variables that apply to this specific level
        variables = Variables.objects.filter(
            game=level.game, level=level, scope="single-level"
        ).order_by("name")

        # Also get variables that apply to all levels
        all_level_vars = Variables.objects.filter(
            game=level.game, scope="all-levels"
        ).order_by("name")

        # Combine both querysets
        all_variables = list(variables) + list(all_level_vars)

        variables_data = []
        for var in all_variables:
            var_data = {
                "id": var.id,
                "name": var.name,
                "slug": var.slug,
                "scope": var.scope,
                "all_cats": var.all_cats,
                "hidden": var.hidden,
            }

            if "values" in embed_fields:
                values = VariableValues.objects.filter(var=var).order_by("name")
                var_data["values"] = [
                    {
                        "value": val.value,
                        "name": val.name,
                        "slug": val.slug,
                        "hidden": val.hidden,
                        "rules": val.rules,
                    }
                    for val in values
                ]

            variables_data.append(var_data)

        embed_key = "values" if "values" in embed_fields else "variables"
        embeds[embed_key] = variables_data

    return embeds


@levels_router.get(
    "/{id}",
    response=Union[LevelSchema, ErrorResponse],
    summary="Get Level by ID",
    description="""
    Retrieve a single level by its ID.

    **Supported Embeds:**
    - `game`: Include the game this level belongs to
    - `variables`: Include level-specific variables
    - `values`: Include variables with their possible values

    **Examples:**
    - `/levels/592pxj8d` - Basic level data
    - `/levels/592pxj8d?embed=game` - Include game data
    - `/levels/592pxj8d?embed=values` - Include variables with values
    """,
    auth=read_only_auth,
)
def get_level(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
) -> Union[LevelSchema, ErrorResponse]:
    """Get a single level by ID."""
    if len(id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("levels", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["game", "variables", "values"]},
                code=400,
            )

    try:
        level = Levels.objects.filter(id__iexact=id).first()
        if not level:
            return ErrorResponse(error="Level ID does not exist", code=404)

        level_data = LevelSchema.model_validate(level)

        if embed_fields:
            embed_data = apply_level_embeds(level, embed_fields)
            for field, data in embed_data.items():
                setattr(level_data, field, data)

        return level_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve level", details={"exception": str(e)}, code=500
        )


@levels_router.get(
    "/all",
    response=Union[List[LevelSchema], ErrorResponse],
    summary="Get All Levels",
    description="""
    Retrieve all levels with optional filtering.

    **Query Parameters:**
    - `game_id`: Filter by specific game ID
    - `embed`: Include related data
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)
    """,
    auth=read_only_auth,
)
def get_all_levels(
    request: HttpRequest,
    game_id: Optional[str] = Query(None, description="Filter by game ID"),
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Union[List[LevelSchema], ErrorResponse]:
    """Get all levels with optional filtering."""
    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("levels", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}", code=400
            )

    try:
        queryset = Levels.objects.all().order_by("name")

        if game_id:
            queryset = queryset.filter(game__id=game_id)

        levels = queryset[offset : offset + limit]

        level_schemas = []
        for level in levels:
            level_data = LevelSchema.model_validate(level)

            if embed_fields:
                embed_data = apply_level_embeds(level, embed_fields)
                for field, data in embed_data.items():
                    setattr(level_data, field, data)

            level_schemas.append(level_data)

        return level_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve levels", details={"exception": str(e)}, code=500
        )


@levels_router.post(
    "/",
    response=Union[LevelSchema, ErrorResponse],
    summary="Create Level",
    auth=api_key_required,
)
def create_level(
    request: HttpRequest,
    level_data: LevelCreateSchema,
) -> Union[LevelSchema, ErrorResponse]:
    """Create a new level."""
    try:
        game = Games.objects.filter(id=level_data.game_id).first()
        if not game:
            return ErrorResponse(error="Game does not exist", code=400)

        level = Levels.objects.create(
            game=game, **{k: v for k, v in level_data.dict().items() if k != "game_id"}
        )

        return LevelSchema.model_validate(level)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create level", details={"exception": str(e)}, code=500
        )


@levels_router.put(
    "/{id}",
    response=Union[LevelSchema, ErrorResponse],
    summary="Update Level",
    auth=api_key_required,
)
def update_level(
    request: HttpRequest,
    id: str,
    level_data: LevelUpdateSchema,
) -> Union[LevelSchema, ErrorResponse]:
    """Update an existing level."""
    try:
        level = Levels.objects.filter(id__iexact=id).first()
        if not level:
            return ErrorResponse(error="Level does not exist", code=404)

        update_data = level_data.dict(exclude_unset=True)
        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(error="Game does not exist", code=400)
            level.game = game
            del update_data["game_id"]

        for field, value in update_data.items():
            setattr(level, field, value)

        level.save()
        return LevelSchema.model_validate(level)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update level", details={"exception": str(e)}, code=500
        )


@levels_router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Level",
    auth=api_key_required,
)
def delete_level(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    """Delete a level."""
    try:
        level = Levels.objects.filter(id__iexact=id).first()
        if not level:
            return ErrorResponse(error="Level does not exist", code=404)

        name = level.name
        level.delete()
        return {"message": f"Level '{name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete level", details={"exception": str(e)}, code=500
        )
