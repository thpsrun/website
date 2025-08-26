from typing import Any, Dict, List, Union

from django.db.models import Case, Prefetch, Q, When
from django.http import HttpRequest
from ninja import Path, Router
from srl.models import Games, Levels, Variables

from api.auth import read_only_auth
from api.schemas.base import ErrorResponse

game_levels_router = Router(tags=["Website - Game Levels"])


@game_levels_router.get(
    "/game/{game_id}/levels",
    response=Union[List[Dict[str, Any]], ErrorResponse],
    summary="Get Game Levels with Variables",
    description="""
    Get all levels for a game with their variables and values.
    Used for Individual Level (IL) speedrun interfaces.

    **Features:**
    - Custom level ordering using existing ordering system
    - Includes level-specific variables
    - Optimized for IL category selection

    **URL Change:**
    - DRF: `/website/levels/{id}` 
    - Ninja: `/website/game/{game_id}/levels` (more RESTful)
    """,
    auth=read_only_auth,
)
def get_game_levels(
    request: HttpRequest, game_id: str = Path(..., description="Game ID or slug")
) -> Union[List[Dict[str, Any]], ErrorResponse]:
    """Get levels for a game with variables (converted from Web_Levels.py)."""
    if len(game_id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return ErrorResponse(error="Game not found", code=404)

        # Import the ordering function from the existing system
        from api.ordering import get_ordered_level_names

        get_order = get_ordered_level_names(game.slug)
        level_order = Case(
            *(When(name=name, then=position) for position, name in enumerate(get_order))
        )

        levels = (
            Levels.objects.filter(game=game)
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related("variablevalues_set"),
                )
            )
            .order_by(level_order)
        )

        # Convert to response format
        levels_data = []
        for level in levels:
            variables_data = []
            for variable in level.variables_set.all():
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

            levels_data.append(
                {
                    "id": level.id,
                    "name": level.name,
                    "slug": level.slug,
                    "url": level.url,
                    "rules": level.rules,
                    "variables": variables_data,
                }
            )

        return levels_data

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve game levels",
            details={"exception": str(e)},
            code=500,
        )