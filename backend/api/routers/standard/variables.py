from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Categories, Games, Levels, Variables, VariableValues

from api.auth.api_key import api_key_required, read_only_auth
from api.schemas.base import ErrorResponse
from api.schemas.variables import (
    VariableCreateSchema,
    VariableSchema,
    VariableUpdateSchema,
    VariableWithValuesSchema,
)

variables_router = Router(tags=["Variables"])


def apply_variable_embeds(
    variable: Variables,
    embed_fields: List[str],
) -> dict:
    """Apply requested embeds to a variable instance."""
    embeds = {}

    if "game" in embed_fields:
        if variable.game:
            embeds["game"] = {
                "id": variable.game.id,
                "name": variable.game.name,
                "slug": variable.game.slug,
                "release": variable.game.release.isoformat(),
                "boxart": variable.game.boxart,
                "twitch": variable.game.twitch,
                "defaulttime": variable.game.defaulttime,
                "idefaulttime": variable.game.idefaulttime,
                "pointsmax": variable.game.pointsmax,
                "ipointsmax": variable.game.ipointsmax,
            }

    if "category" in embed_fields:
        if variable.cat:
            embeds["category"] = {
                "id": variable.cat.id,
                "name": variable.cat.name,
                "slug": variable.cat.slug,
                "type": variable.cat.type,
                "url": variable.cat.url,
                "rules": variable.cat.rules,
                "appear_on_main": variable.cat.appear_on_main,
                "hidden": variable.cat.hidden,
            }

    if "level" in embed_fields:
        if variable.level:
            embeds["level"] = {
                "id": variable.level.id,
                "name": variable.level.name,
                "slug": variable.level.slug,
                "url": variable.level.url,
                "rules": variable.level.rules,
            }

    return embeds


@variables_router.get(
    "/{id}",
    response=Union[VariableWithValuesSchema, ErrorResponse],
    summary="Get Variable by ID",
    description="""
    Retrieve a single variable with its possible values.

    **Supported Embeds:**
    - `game`: Include the game this variable belongs to
    - `category`: Include the specific category (if not all_cats)
    - `level`: Include the specific level (if scope=single-level)

    **Examples:**
    - `/variables/5lygdn8q` - Variable with its values
    - `/variables/5lygdn8q?embed=game,category` - Include game and category
    """,
    auth=read_only_auth,
)
def get_variable(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
) -> Union[VariableWithValuesSchema, ErrorResponse]:
    """Get a single variable by ID with its values."""
    if len(id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        # Variables support: game, category, level
        valid_embeds = {"game", "category", "level"}
        invalid_embeds = [field for field in embed_fields if field not in valid_embeds]
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["game", "category", "level"]},
                code=400,
            )

    try:
        variable = Variables.objects.filter(id__iexact=id).first()
        if not variable:
            return ErrorResponse(error="Variable ID does not exist", code=404)

        # Get variable values
        values = VariableValues.objects.filter(var=variable).order_by("name")

        # Build response data
        variable_data = {
            "id": variable.id,
            "name": variable.name,
            "slug": variable.slug,
            "scope": variable.scope,
            "all_cats": variable.all_cats,
            "hidden": variable.hidden,
            "values": [
                {
                    "value": val.value,
                    "name": val.name,
                    "slug": val.slug,
                    "hidden": val.hidden,
                    "rules": val.rules,
                }
                for val in values
            ],
        }

        # Apply embeds
        if embed_fields:
            embed_data = apply_variable_embeds(variable, embed_fields)
            variable_data.update(embed_data)

        return VariableWithValuesSchema(**variable_data)

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve variable", details={"exception": str(e)}, code=500
        )


@variables_router.get(
    "/all",
    response=Union[List[VariableSchema], ErrorResponse],
    summary="Get All Variables",
    description="""
    Retrieve variables with flexible filtering options.

    **Query Parameters:**
    - `game_id`: Filter by specific game
    - `category_id`: Filter by specific category
    - `level_id`: Filter by specific level
    - `scope`: Filter by scope (global, full-game, all-levels, single-level)
    - `embed`: Include related data
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Note:** This endpoint returns variables without their values for performance.
    Use the single variable endpoint to get values.
    """,
    auth=read_only_auth,
)
def get_all_variables(
    request: HttpRequest,
    game_id: Optional[str] = Query(None, description="Filter by game ID"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    level_id: Optional[str] = Query(None, description="Filter by level ID"),
    scope: Optional[str] = Query(
        None,
        description="Filter by scope",
        pattern="^(global|full-game|all-levels|single-level)$",
    ),
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Union[List[VariableSchema], ErrorResponse]:
    """Get variables with filtering (without values for performance)."""
    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        valid_embeds = {"game", "category", "level"}
        invalid_embeds = [field for field in embed_fields if field not in valid_embeds]
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}", code=400
            )

    try:
        queryset = Variables.objects.all().order_by("name")

        # Apply filters
        if game_id:
            queryset = queryset.filter(game__id=game_id)
        if category_id:
            queryset = queryset.filter(cat__id=category_id)
        if level_id:
            queryset = queryset.filter(level__id=level_id)
        if scope:
            queryset = queryset.filter(scope=scope)

        variables = queryset[offset : offset + limit]

        variable_schemas = []
        for variable in variables:
            variable_data = VariableSchema.model_validate(variable)

            if embed_fields:
                embed_data = apply_variable_embeds(variable, embed_fields)
                for field, data in embed_data.items():
                    setattr(variable_data, field, data)

            variable_schemas.append(variable_data)

        return variable_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve variables",
            details={"exception": str(e)},
            code=500,
        )


@variables_router.post(
    "/",
    response=Union[VariableSchema, ErrorResponse],
    summary="Create Variable",
    description="""
    Create a new variable with validation for scope and relationship constraints.

    **Validation Rules:**
    - Must have either `category_id` OR `all_cats=true`
    - If `scope=single-level`, must provide `level_id`
    - If `level_id` provided, `scope` must be `single-level`
    """,
    auth=api_key_required,
)
def create_variable(
    request: HttpRequest,
    variable_data: VariableCreateSchema,
) -> Union[VariableSchema, ErrorResponse]:
    """Create a new variable with validation."""
    try:
        # Validate game exists
        game = Games.objects.filter(id=variable_data.game_id).first()
        if not game:
            return ErrorResponse(error="Game does not exist", code=400)

        # Validate category/all_cats constraint
        category = None
        if variable_data.category_id and variable_data.all_cats:
            return ErrorResponse(
                error="Cannot set both category_id and all_cats=true", code=400
            )
        elif variable_data.category_id:
            category = Categories.objects.filter(id=variable_data.category_id).first()
            if not category:
                return ErrorResponse(error="Category does not exist", code=400)
        elif not variable_data.all_cats:
            return ErrorResponse(
                error="Must provide either category_id or set all_cats=true", code=400
            )

        # Validate level/scope constraint
        level = None
        if variable_data.level_id:
            if variable_data.scope != "single-level":
                return ErrorResponse(
                    error="If level_id is provided, scope must be 'single-level'",
                    code=400,
                )
            level = Levels.objects.filter(id=variable_data.level_id).first()
            if not level:
                return ErrorResponse(error="Level does not exist", code=400)
        elif variable_data.scope == "single-level":
            return ErrorResponse(
                error="If scope is 'single-level', level_id must be provided", code=400
            )

        # Create variable
        create_data = variable_data.dict(exclude={"game_id", "category_id", "level_id"})
        variable = Variables.objects.create(
            game=game, cat=category, level=level, **create_data
        )

        return VariableSchema.model_validate(variable)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create variable", details={"exception": str(e)}, code=500
        )


@variables_router.put(
    "/{id}",
    response=Union[VariableSchema, ErrorResponse],
    summary="Update Variable",
    auth=api_key_required,
)
def update_variable(
    request: HttpRequest,
    id: str,
    variable_data: VariableUpdateSchema,
) -> Union[VariableSchema, ErrorResponse]:
    """Update an existing variable."""
    try:
        variable = Variables.objects.filter(id__iexact=id).first()
        if not variable:
            return ErrorResponse(error="Variable does not exist", code=404)

        update_data = variable_data.dict(exclude_unset=True)

        # Handle relationship updates with validation
        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(error="Game does not exist", code=400)
            variable.game = game
            del update_data["game_id"]

        if "category_id" in update_data:
            if update_data["category_id"]:
                category = Categories.objects.filter(
                    id=update_data["category_id"]
                ).first()
                if not category:
                    return ErrorResponse(error="Category does not exist", code=400)
                variable.cat = category
            else:
                variable.cat = None
            del update_data["category_id"]

        if "level_id" in update_data:
            if update_data["level_id"]:
                level = Levels.objects.filter(id=update_data["level_id"]).first()
                if not level:
                    return ErrorResponse(error="Level does not exist", code=400)
                variable.level = level
            else:
                variable.level = None
            del update_data["level_id"]

        # Update other fields
        for field, value in update_data.items():
            setattr(variable, field, value)

        variable.save()

        # Run model validation (this will check the complex constraints)
        try:
            variable.clean()
        except Exception as validation_error:
            return ErrorResponse(
                error="Validation failed",
                details={"validation_error": str(validation_error)},
                code=400,
            )

        return VariableSchema.model_validate(variable)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update variable", details={"exception": str(e)}, code=500
        )


@variables_router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Variable",
    auth=api_key_required,
)
def delete_variable(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    """Delete a variable and its associated values."""
    try:
        variable = Variables.objects.filter(id__iexact=id).first()
        if not variable:
            return ErrorResponse(error="Variable does not exist", code=404)

        name = variable.name
        variable.delete()  # This will cascade delete VariableValues
        return {"message": f"Variable '{name}' and its values deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete variable", details={"exception": str(e)}, code=500
        )
