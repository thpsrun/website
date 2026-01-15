from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Categories, Games, Levels, Variables, VariableValues

from api.docs.variables import (
    VARIABLES_DELETE,
    VARIABLES_GET,
    VARIABLES_POST,
    VARIABLES_PUT,
)
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse
from api.schemas.variables import (
    VariableCreateSchema,
    VariableSchema,
    VariableUpdateSchema,
    VariableWithValuesSchema,
)

router = Router(tags=["Variables"])


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
                "archive": variable.cat.archive,
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


@router.get(
    "/{id}",
    response=Union[VariableWithValuesSchema, ErrorResponse],
    summary="Get Variable by ID",
    description="""
    Retrieve a single variable by its ID, including optional embedding.

    **Supported Embeds:**
    - `game`: Include metadata related to the game
    - `category`: Include metadata related to the category
    - `level`: Include metadata related to the level

    **Examples:**
    - `/variables/5lygdn8q` - Get variable by ID
    - `/variables/5lygdn8q?embed=game` - Get variable with game data
    - `/variables/5lygdn8q?embed=game,category,level` - Get variable with all embeds
    """,
    auth=public_auth,
    openapi_extra=VARIABLES_GET,
)
def get_variable(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[VariableWithValuesSchema, ErrorResponse]:
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
            return ErrorResponse(
                error="Variable ID does not exist",
                details=None,
                code=404,
            )

        values = VariableValues.objects.filter(var=variable).order_by("name")

        variable_data = {
            "id": variable.id,
            "name": variable.name,
            "slug": variable.slug,
            "scope": variable.scope,
            "archive": variable.archive,
            "values": [
                {
                    "value": val.value,
                    "name": val.name,
                    "slug": val.slug,
                    "archive": val.archive,
                    "rules": val.rules,
                }
                for val in values
            ],
        }

        if embed_fields:
            embed_data = apply_variable_embeds(variable, embed_fields)
            variable_data.update(embed_data)

        return VariableWithValuesSchema(**variable_data)

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve variable",
            details={"exception": str(e)},
            code=500,
        )


@router.get(
    "/all",
    response=Union[List[VariableSchema], ErrorResponse],
    summary="Get All Variables",
    description="""
    Retrieve all variables within the `Variables` object, including optional embedding and filtering.

    **Supported Embeds:**
    - `game`: Include metadata of the game the variable belongs to
    - `category`: Include metadata of the category the variable belongs to
    - `level`: Include metadata of the level the variable belongs to

    **Supported Parameters:**
    - `game_id`: Filter by specific game ID or slug
    - `category_id`: Filter by specific category ID
    - `level_id`: Filter by specific level ID
    - `scope`: Filter by scope (`global`, `full-game`, `all-levels`, `single-level`)
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/variables/all` - Get all variables
    - `/variables/all?game_id=thps4` - Get all variables for THPS4
    - `/variables/all?scope=full-game` - Get all full-game variables
    - `/variables/all?game_id=thps4&embed=game,category` - Get THPS4 variables with embeds
    """,
    auth=public_auth,
)
def get_all_variables(
    request: HttpRequest,
    game_id: Optional[str] = Query(
        None,
        description="Filter by game ID",
    ),
    category_id: Optional[str] = Query(
        None,
        description="Filter by category ID",
    ),
    level_id: Optional[str] = Query(
        None,
        description="Filter by level ID",
    ),
    scope: Optional[str] = Query(
        None,
        description="Filter by scope",
        pattern="^(global|full-game|all-levels|single-level)$",
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
) -> Union[List[VariableSchema], ErrorResponse]:
    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        valid_embeds = {"game", "category", "level"}
        invalid_embeds = [field for field in embed_fields if field not in valid_embeds]
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    try:
        queryset = Variables.objects.all().order_by("name")

        # If parameters are fulfilled by the client, this will further
        # drill down what the client is looking for.
        if game_id:
            queryset = queryset.filter(game__id=game_id)
        if category_id:
            queryset = queryset.filter(cat__id=category_id)
        if level_id:
            queryset = queryset.filter(level__id=level_id)
        if scope:
            queryset = queryset.filter(scope=scope)

        variables = queryset[offset : offset + limit]

        # For each of the variables, it will go through and add additional context
        # if the embed option is provided. If not, it will provide basic information
        # (e.g. the ID of the value), with additional information provided if declared.
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


@router.post(
    "/",
    response=Union[VariableSchema, ErrorResponse],
    summary="Create Variable",
    description="""
    Creates a brand new variable with validation for scope and relationship constraints.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Request Body:**
    - `game_id` (str): Game ID this variable belongs to.
    - `name` (str): Variable name.
    - `scope` (str): Where this variable applies (`global`, `full-game`, `all-levels`, `single-level`).
    - `archive` (bool): Whether variable is archived/hidden from listings.
    - `category_id` (Optional[str]): Specific category ID (if not all_cats).
    - `level_id` (Optional[str]): Specific level ID (required if scope is `single-level`).
    """,
    auth=moderator_auth,
    openapi_extra=VARIABLES_POST,
)
def create_variable(
    request: HttpRequest,
    variable_data: VariableCreateSchema,
) -> Union[VariableSchema, ErrorResponse]:
    try:
        game = Games.objects.filter(id=variable_data.game_id).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=400,
            )

        category = None
        if variable_data.category_id:
            category = Categories.objects.filter(id=variable_data.category_id).first()
            if not category:
                return ErrorResponse(
                    error="Category does not exist",
                    details=None,
                    code=400,
                )

        level = None
        if variable_data.level_id:
            if variable_data.scope != "single-level":
                return ErrorResponse(
                    error="If level_id is provided, scope must be 'single-level'",
                    details=None,
                    code=400,
                )
            level = Levels.objects.filter(id=variable_data.level_id).first()
            if not level:
                return ErrorResponse(
                    error="Level does not exist",
                    details=None,
                    code=400,
                )
        elif variable_data.scope == "single-level":
            return ErrorResponse(
                error="If scope is 'single-level', level_id must be provided",
                details=None,
                code=400,
            )

        create_data = variable_data.model_dump(
            exclude={"game_id", "category_id", "level_id"}
        )
        variable = Variables.objects.create(
            game=game, cat=category, level=level, **create_data
        )

        return VariableSchema.model_validate(variable)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create variable",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[VariableSchema, ErrorResponse],
    summary="Update Variable",
    description="""
    Updates the variable based on its unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Supported Parameters:**
    - `id` (str): Unique ID of the variable being updated.

    **Request Body:**
    - `game_id` (Optional[str]): Updated game ID.
    - `name` (Optional[str]): Updated variable name.
    - `scope` (Optional[str]): Updated scope (`global`, `full-game`, `all-levels`, `single-level`).
    - `all_cats` (Optional[bool]): Updated all_cats flag.
    - `archive` (Optional[bool]): Updated archive status.
    - `category_id` (Optional[str]): Updated category ID.
    - `level_id` (Optional[str]): Updated level ID.
    """,
    auth=moderator_auth,
    openapi_extra=VARIABLES_PUT,
)
def update_variable(
    request: HttpRequest,
    id: str,
    variable_data: VariableUpdateSchema,
) -> Union[VariableSchema, ErrorResponse]:
    try:
        variable = Variables.objects.filter(id__iexact=id).first()
        if not variable:
            return ErrorResponse(
                error="Variable does not exist",
                details=None,
                code=404,
            )

        update_data = variable_data.model_dump(exclude_unset=True)

        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(
                    error="Game does not exist",
                    details=None,
                    code=400,
                )
            variable.game = game
            del update_data["game_id"]

        if "category_id" in update_data:
            if update_data["category_id"]:
                category = Categories.objects.filter(
                    id=update_data["category_id"]
                ).first()
                if not category:
                    return ErrorResponse(
                        error="Category does not exist",
                        details=None,
                        code=400,
                    )
                variable.cat = category
            else:
                variable.cat = None  # type: ignore
            del update_data["category_id"]

        if "level_id" in update_data:
            if update_data["level_id"]:
                level = Levels.objects.filter(id=update_data["level_id"]).first()
                if not level:
                    return ErrorResponse(
                        error="Level does not exist",
                        details=None,
                        code=400,
                    )
                variable.level = level
            else:
                variable.level = None
            del update_data["level_id"]

        for field, value in update_data.items():
            setattr(variable, field, value)

        variable.save()

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
            error="Failed to update variable",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Variable",
    description="""
    Deletes the selected variable by its ID. **Also deletes associated values.**

    **REQUIRES ADMIN ACCESS.**

    **Supported Parameters:**
    - `id` (str): Unique ID of the variable being deleted.
    """,
    auth=admin_auth,
    openapi_extra=VARIABLES_DELETE,
)
def delete_variable(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        variable = Variables.objects.filter(id__iexact=id).first()
        if not variable:
            return ErrorResponse(
                error="Variable does not exist",
                details=None,
                code=404,
            )

        name = variable.name
        variable.delete()
        return {"message": f"Variable '{name}' and its values deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete variable",
            details={"exception": str(e)},
            code=500,
        )
