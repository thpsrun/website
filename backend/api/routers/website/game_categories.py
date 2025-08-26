from typing import Any, Dict, List, Union

from django.db.models import Case, IntegerField, Prefetch, Q, Value, When
from django.http import HttpRequest
from ninja import Path, Router
from srl.models import Categories, Games, Variables

from api.auth import read_only_auth
from api.schemas.base import ErrorResponse

game_categories_router = Router(tags=["Website - Game Categories"])


@game_categories_router.get(
    "/game/{game_id}/categories",
    response=Union[List[Dict[str, Any]], ErrorResponse],
    summary="Get Game Categories with Variables",
    description="""
    Get all categories for a game with their variables and values.
    Optimized for the category selection interface.

    **Features:**
    - Custom category ordering (Any%, 100%, etc.)
    - Includes all variables and their possible values
    - Optimized database queries with prefetch

    **URL Change:**
    - DRF: `/website/categories/{id}`
    - Ninja: `/website/game/{game_id}/categories` (more RESTful)
    """,
    auth=read_only_auth,
)
def get_game_categories(
    request: HttpRequest, game_id: str = Path(..., description="Game ID or slug")
) -> Union[List[Dict[str, Any]], ErrorResponse]:
    """Get categories for a game with variables."""
    if len(game_id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return ErrorResponse(error="Game not found", code=404)

        # Get categories with custom ordering (same as DRF version)
        categories = (
            Categories.objects.filter(game=game)
            .annotate(
                order=Case(
                    When(name__istartswith="Any%", then=Value(1)),
                    When(name__istartswith="All Goals & Golds", then=Value(2)),
                    When(name__istartswith="Story", then=Value(3)),
                    When(name__istartswith="Classic", then=Value(4)),
                    When(name__istartswith="0%", then=Value(5)),
                    When(name__istartswith="100%", then=Value(7)),
                    default=Value(6),
                    output_field=IntegerField(),
                )
            )
            .order_by("order", "name")
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related("variablevalues_set"),
                )
            )
        )

        # Convert to response format
        categories_data = []
        for category in categories:
            variables_data = []
            for variable in category.variables_set.all():
                values_data = [
                    {
                        "value": val.value,
                        "name": val.name,
                        "slug": val.slug,
                        "hidden": val.hidden,
                        "rules": val.rules,
                    }
                    for val in variable.variablevalues_set.all()
                ]

                variables_data.append(
                    {
                        "id": variable.id,
                        "name": variable.name,
                        "slug": variable.slug,
                        "scope": variable.scope,
                        "all_cats": variable.all_cats,
                        "hidden": variable.hidden,
                        "values": values_data,
                    }
                )

            categories_data.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "type": category.type,
                    "url": category.url,
                    "rules": category.rules,
                    "appear_on_main": category.appear_on_main,
                    "hidden": category.hidden,
                    "variables": variables_data,
                }
            )

        return categories_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve game categories",
            details={"exception": str(e)},
            code=500,
        )