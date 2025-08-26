from typing import List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Categories, Games, Variables, VariableValues

from api.auth.api_key import api_key_required, read_only_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.categories import (
    CategoryCreateSchema,
    CategorySchema,
    CategoryUpdateSchema,
)

categories_router = Router(tags=["Categories"])


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


@categories_router.get(
    "/{id}",
    response=Union[CategorySchema, ErrorResponse],
    summary="Get Category by ID",
    description="""
    Retrieves a single category from the database based upon its ID.

    Supported Embeds:
    - `game`: Includes the metadata of the game the category belongs to.
    - `variables`: Include some of the metadata of the variables belonging to this category.
    - `values`: Include all of the metadata for each variable and its values.

    Examples:
    - `/categories/rklge08d` - Basic category data
    - `/categories/rklge08d?embed=game` - Include game data
    - `/categories/rklge08d?embed=values` - Include variables with values
    """,
    auth=read_only_auth,
)
def get_category(
    request: HttpRequest,
    id: str,
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
) -> Union[CategorySchema, ErrorResponse]:
    if len(id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    # Parse embeds
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
            return ErrorResponse(error="Category ID does not exist", code=404)

        category_data = CategorySchema.model_validate(category)

        if embed_fields:
            embed_data = category_embeds(category, embed_fields)
            for field, data in embed_data.items():
                setattr(category_data, field, data)

        return category_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve category", details={"exception": str(e)}, code=500
        )


@categories_router.get(
    "/all",
    response=Union[List[CategorySchema], ErrorResponse],
    summary="Get All Categories",
    description="""
    Retrieve all categories with optional filtering and embeds.

    **Query Parameters:**
    - `game_id`: Filter by specific game ID
    - `type`: Filter by category type (per-game or per-level)
    - `embed`: Include related data
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)
    """,
    auth=read_only_auth,
)
def get_all_categories(
    request: HttpRequest,
    game_id: Optional[str] = Query(None, description="Filter by game ID"),
    type: Optional[str] = Query(
        None, description="Filter by type", pattern="^(per-game|per-level)$"
    ),
    embed: Optional[str] = Query(None, description="Comma-separated embeds"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Union[List[CategorySchema], ErrorResponse]:
    """Get all categories with optional filtering."""
    # Parse embeds
    embed_fields = []
    if embed:
        embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
        invalid_embeds = validate_embeds("categories", embed_fields)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}", code=400
            )

    try:
        # Build queryset
        queryset = Categories.objects.all().order_by("name")

        if game_id:
            queryset = queryset.filter(game__id=game_id)
        if type:
            queryset = queryset.filter(type=type)

        # Apply pagination
        categories = queryset[offset : offset + limit]

        # Convert to schemas
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


@categories_router.post(
    "/",
    response=Union[CategorySchema, ErrorResponse],
    summary="Create Category",
    auth=api_key_required,
)
def create_category(
    request: HttpRequest,
    category_data: CategoryCreateSchema,
) -> Union[CategorySchema, ErrorResponse]:
    """Create a new category."""
    try:
        # Validate game exists
        game = Games.objects.filter(id=category_data.game_id).first()
        if not game:
            return ErrorResponse(error="Game does not exist", code=400)

        # Create category
        category = Categories.objects.create(
            game=game,
            **{k: v for k, v in category_data.dict().items() if k != "game_id"},
        )

        return CategorySchema.model_validate(category)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create category", details={"exception": str(e)}, code=500
        )


@categories_router.put(
    "/{id}",
    response=Union[CategorySchema, ErrorResponse],
    summary="Update Category",
    auth=api_key_required,
)
def update_category(
    request: HttpRequest,
    id: str,
    category_data: CategoryUpdateSchema,
) -> Union[CategorySchema, ErrorResponse]:
    """Update an existing category."""
    try:
        category = Categories.objects.filter(id__iexact=id).first()
        if not category:
            return ErrorResponse(error="Category does not exist", code=404)

        # Update fields
        update_data = category_data.dict(exclude_unset=True)
        if "game_id" in update_data:
            game = Games.objects.filter(id=update_data["game_id"]).first()
            if not game:
                return ErrorResponse(error="Game does not exist", code=400)
            category.game = game
            del update_data["game_id"]

        for field, value in update_data.items():
            setattr(category, field, value)

        category.save()
        return CategorySchema.model_validate(category)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update category", details={"exception": str(e)}, code=500
        )


@categories_router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Category",
    auth=api_key_required,
)
def delete_category(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    """Delete a category."""
    try:
        category = Categories.objects.filter(id__iexact=id).first()
        if not category:
            return ErrorResponse(error="Category does not exist", code=404)

        name = category.name
        category.delete()
        return {"message": f"Category '{name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete category", details={"exception": str(e)}, code=500
        )
