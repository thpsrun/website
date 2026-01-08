from typing import List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Categories, Games, Variables, VariableValues

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.categories import (
    CategoryCreateSchema,
    CategorySchema,
    CategoryUpdateSchema,
)

router = Router()

# START OPENAPI DOCUMENTATION #
CATEGORIES_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "rklge08d",
                        "name": "Any%",
                        "slug": "any",
                        "type": "per-game",
                        "url": "https://speedrun.com/thps4/full_game#Any",
                        "rules": "Rulez.",
                        "appear_on_main": True,
                        "hidden": False,
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
                        "variables": [
                            {
                                "id": "fdsw34df",
                                "name": "Platform",
                                "slug": "platform",
                                "scope": "full-game",
                                "all_cats": True,
                                "hidden": False,
                                "values": [
                                    {
                                        "value": "pcdfsf",
                                        "name": "PC",
                                        "slug": "pc",
                                        "hidden": False,
                                        "rules": "",
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Category could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "rklge08d",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Category ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,variables,values",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: game, variables, values",
        },
    ],
}

CATEGORIES_POST = {
    "responses": {
        201: {
            "description": "Category created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "rklge08d",
                        "name": "Any%",
                        "slug": "any",
                        "type": "per-game",
                        "url": "https://speedrun.com/thps4/full_game#Any",
                        "rules": "Rulez.",
                        "appear_on_main": True,
                        "hidden": False,
                    }
                }
            },
        },
        400: {"description": "Invalid request data or game does not exist."},
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
                    "required": ["name", "game_id"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Any%",
                            "description": "NAME OF CATEGORY",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "GAME ID THIS CATEGORY BELONGS TO",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["per-game", "per-level"],
                            "example": "per-game",
                            "description": "CATEGORY TYPE",
                        },
                        "rules": {
                            "type": "string",
                            "example": "Rulez.",
                            "description": "CATEGORY RULES",
                        },
                        "appear_on_main": {
                            "type": "boolean",
                            "example": True,
                            "description": "WHETHER CATEGORY APPEARS ON MAIN PAGE",
                        },
                        "hidden": {
                            "type": "boolean",
                            "example": False,
                            "description": "WHETHER CATEGORY IS HIDDEN",
                        },
                    },
                },
                "example": {
                    "name": "Any%",
                    "game_id": "n2680o1p",
                    "type": "per-game",
                    "rules": "Rulez.",
                    "appear_on_main": True,
                    "hidden": False,
                },
            }
        },
    },
}

CATEGORIES_PUT = {
    "responses": {
        200: {
            "description": "Category updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "rklge08d",
                        "name": "Any%",
                        "slug": "any",
                        "type": "per-game",
                        "url": "https://speedrun.com/thps4/full_game#Any",
                        "rules": "Complete the game as fast as possible.",
                        "appear_on_main": True,
                        "hidden": False,
                    }
                }
            },
        },
        400: {"description": "Invalid request data or game does not exist."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Category does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "rklge08d",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Category ID to update",
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
                            "example": "Any%",
                            "description": "UPDATED CATEGORY NAME",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "UPDATED GAME ID",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["per-game", "per-level"],
                            "example": "per-game",
                            "description": "UPDATED CATEGORY TYPE",
                        },
                        "rules": {
                            "type": "string",
                            "example": "Complete the game as fast as possible.",
                            "description": "UPDATED CATEGORY RULES",
                        },
                        "appear_on_main": {
                            "type": "boolean",
                            "example": True,
                            "description": "UPDATED MAIN PAGE APPEARANCE",
                        },
                        "hidden": {
                            "type": "boolean",
                            "example": False,
                            "description": "UPDATED HIDDEN STATUS",
                        },
                    },
                },
                "example": {
                    "name": "Any%",
                    "rules": "Complete the game as fast as possible with new rules.",
                    "appear_on_main": True,
                },
            }
        },
    },
}

CATEGORIES_DELETE = {
    "responses": {
        200: {
            "description": "Category deleted successfully!",
            "content": {
                "application/json": {
                    "example": {"message": "Category 'Any%' deleted successfully"}
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Category does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "rklge08d",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Category ID to delete",
        },
    ],
}

CATEGORIES_ALL = {
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
                        },
                        {
                            "id": "xd1m508k",
                            "name": "100%",
                            "slug": "100",
                            "type": "per-game",
                            "url": "https://speedrun.com/thps4/full_game#100",
                            "rules": "Rulez.",
                            "appear_on_main": True,
                            "hidden": False,
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
            "description": "Filter by game ID",
        },
        {
            "name": "type",
            "in": "query",
            "example": "per-game",
            "schema": {"type": "string", "pattern": "^(per-game|per-level)$"},
            "description": "Filter by category type",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,variables",
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


def category_embeds(
    category: Categories,
    embed_fields: List[str],
) -> dict:
    """When requested in the `embed_fields` of a category instance, this will apply the embeds."""
    embeds = {}

    if "game" in embed_fields:
        if category.game:
            embeds["game"] = {
                "id": category.game.id,
                "name": category.game.name,
                "slug": category.game.slug,
                "release": category.game.release.isoformat(),
                "boxart": category.game.boxart,
                "twitch": category.game.twitch,
                "defaulttime": category.game.defaulttime,
                "idefaulttime": category.game.idefaulttime,
                "pointsmax": category.game.pointsmax,
                "ipointsmax": category.game.ipointsmax,
            }

    if "variables" in embed_fields or "values" in embed_fields:
        variables = Variables.objects.filter(
            game=category.game,
            cat=category,
        ).order_by("name")

        variables_data = []
        for var in variables:
            var_data = {
                "id": var.id,
                "name": var.name,
                "slug": var.slug,
                "scope": var.scope,
                "hidden": var.archive,
            }

            if "values" in embed_fields:
                values = VariableValues.objects.filter(var=var).order_by("name")
                var_data["values"] = [
                    {
                        "value": val.value,
                        "name": val.name,
                        "slug": val.slug,
                        "hidden": val.archive,
                        "rules": val.rules,
                    }
                    for val in values
                ]

            variables_data.append(var_data)

        embed_key = "values" if "values" in embed_fields else "variables"
        embeds[embed_key] = variables_data

    return embeds


@router.get(
    "/{id}",
    response=Union[CategorySchema, ErrorResponse],
    summary="Get Category by ID",
    description="""
    Retrieves a single category based upon its ID, including optional embedding.

    **Supported Embeds:**
    - `game`: Includes the metadata of the game the category belongs to
    - `variables`: Include metadata of the variables belonging to this category
    - `values`: Include all metadata for each variable and its values

    **Examples:**
    - `/categories/rklge08d` - Get category by ID
    - `/categories/rklge08d?embed=game` - Get category with game info
    - `/categories/rklge08d?embed=variables,values` - Get category with variables and values
    """,
    auth=read_only_auth,
    openapi_extra=CATEGORIES_GET,
)
def get_category(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds",
    ),
) -> Union[CategorySchema, ErrorResponse]:
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("categories", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details={"valid_embeds": ["game", "variables", "values"]},
                code=400,
            )

    try:
        category = Categories.objects.filter(id__iexact=id).first()
        if not category:
            return ErrorResponse(
                error="Category ID does not exist",
                details=None,
                code=404,
            )

        category_data = CategorySchema.model_validate(category)

        if embed_fields:
            embed_data = category_embeds(category, embed_fields)
            for field, data in embed_data.items():
                setattr(category_data, field, data)

        return category_data
    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve category",
            details={"exception": str(e)},
            code=500,
        )


@router.get(
    "/all",
    response=Union[List[CategorySchema], ErrorResponse],
    summary="Get All Categories",
    description="""
    Retrieves all categories within a `Games` object, including optional embedding and querying.

    **Supported Embeds:**
    - `variables`: Include metadata of the variables belonging to this category
    - `values`: Include all metadata for each variable and its values

    **Supported Parameters:**
    - `game`: Filter by specific game ID or its slug
    - `type`: Filter by category type (`per-game` or `per-level`)
    - `embed`: Comma-separated list of resources to embed
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/categories/all` - Get all categories
    - `/categories/all?game=thps4` - Get all categories for THPS4
    - `/categories/all?type=per-game&limit=20` - Get first 20 full-game categories
    - `/categories/all?game=thps4&embed=variables` - Get THPS4 categories with variables
    """,
    auth=read_only_auth,
    openapi_extra=CATEGORIES_ALL,
)
def get_all_categories(
    request: HttpRequest,
    game: Optional[str] = Query(
        None,
        description="Filter by game ID or slug",
    ),
    type: Optional[str] = Query(
        None,
        description="Filter by type",
        pattern="^(per-game|per-level)$",
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
) -> Union[List[CategorySchema], ErrorResponse]:
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("categories", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    try:
        if game:
            queryset = Categories.objects.filter(
                Q(game_id__iexact=game) | Q(slug__iexact=game)
            ).order_by("name")
        else:
            return ErrorResponse(
                error="Please provide the game's unique ID or slug.",
                details=None,
                code=400,
            )

        if type:
            queryset = queryset.filter(type=type)

        categories = queryset[offset : offset + limit]

        category_schemas = []
        for category in categories:
            category_data = CategorySchema.model_validate(category)

            if embed_fields:
                embed_data = category_embeds(category, embed_fields)
                for field, data in embed_data.items():
                    setattr(category_data, field, data)

            category_schemas.append(category_data)

        return category_schemas
    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve categories",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "/",
    response=Union[CategorySchema, ErrorResponse],
    summary="Create Category",
    description="""
    Creates a brand new category.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=CATEGORIES_POST,
)
def create_category(
    request: HttpRequest,
    category_data: CategoryCreateSchema,
) -> Union[CategorySchema, ErrorResponse]:
    try:
        game = Games.objects.filter(id=category_data.game_id).first()
        if not game:
            return ErrorResponse(
                error="Game does not exist",
                details=None,
                code=404,
            )

        category = Categories.objects.create(
            game=game,
            **{k: v for k, v in category_data.model_dump().items() if k != "game_id"},
        )

        return CategorySchema.model_validate(category)
    except Exception as e:
        return ErrorResponse(
            error="Failed to create category",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[CategorySchema, ErrorResponse],
    summary="Update Category",
    description="""
    Updates the category based on its unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=CATEGORIES_PUT,
)
def update_category(
    request: HttpRequest,
    id: str,
    category_data: CategoryUpdateSchema,
) -> Union[CategorySchema, ErrorResponse]:
    try:
        category = Categories.objects.filter(id__iexact=id).first()
        if not category:
            return ErrorResponse(
                error="Category does not exist",
                details=None,
                code=404,
            )

        update_data = category_data.model_dump(exclude_unset=True)
        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(
                    error="Game does not exist",
                    details=None,
                    code=400,
                )
            category.game = game
            del update_data["game_id"]

        for field, value in update_data.items():
            setattr(category, field, value)

        category.save()
        return CategorySchema.model_validate(category)
    except Exception as e:
        return ErrorResponse(
            error="Failed to update category",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Category",
    description="""
    Deletes the selected category based on its ID.

    **REQUIRES ADMIN ACCESS.**
    """,
    auth=api_admin_check,
    openapi_extra=CATEGORIES_DELETE,
)
def delete_category(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        category = Categories.objects.filter(id__iexact=id).first()
        if not category:
            return ErrorResponse(
                error="Category does not exist",
                details=None,
                code=404,
            )

        name = category.name
        category.delete()
        return {"message": f"Category '{name}' deleted successfully"}
    except Exception as e:
        return ErrorResponse(
            error="Failed to delete category",
            details={"exception": str(e)},
            code=500,
        )
