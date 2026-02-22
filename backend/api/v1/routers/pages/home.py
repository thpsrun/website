from textwrap import dedent
from typing import Annotated, Any

from django.db.models import Case, F, IntegerField, Prefetch, Q, Value, When
from django.http import HttpRequest
from ninja import Query, Router
from ninja.responses import codes_4xx
from pydantic import Field
from srl.models import Categories, Games, Levels, Variables, VariableValues

from api.permissions import public_auth
from api.v1.docs.website import GAME_CATEGORIES_GET, GAME_LEVELS_GET, MAIN_PAGE_GET
from api.v1.routers.decorators import categories_adapter, levels_adapter
from api.v1.routers.utils import cache_response, get_cached_embed
from api.v1.schemas.base import ErrorResponse
from api.v1.schemas.categories import GameCategoryResponseSchema
from api.v1.schemas.levels import GameLevelResponseSchema
from api.v1.schemas.variables import VariableValueSchema, VariableWithValuesSchema

router = Router()


@router.get(
    "/main",
    response={200: dict[str, Any], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Main Page Data",
    description=dedent(
        """
    Get aggregated data for the website main page including latest world records,
    personal bests, and current records for featured categories.

    **Supported Embeds:**
    - `latest-wrs`: Latest 5 world records within the database.
    - `latest-pbs`: Latest 5 personal bests (excluding WRs) within the database.
    - `records`: Current WRs for featured categories.

    **Supported Parameters:**
    - `embed`: Comma-separated list of data types to include (required)

    **Examples:**
    - `/website/main?embed=latest-wrs,latest-pbs` - Recent activity
    - `/website/main?embed=records` - Current world records
    - `/website/main?embed=latest-wrs,latest-pbs,records` - All data

    **Note:** This is an aggregation endpoint optimized for the React frontend homepage.
    """
    ),
    auth=public_auth,
    openapi_extra=MAIN_PAGE_GET,
)
def get_main_page_data(
    request: HttpRequest,
    embed: Annotated[
        str | None,
        Query,
        Field(description="Comma-separated embed types"),
    ] = None,
) -> tuple[int, dict[str, Any] | ErrorResponse]:
    if not embed:
        return 400, ErrorResponse(
            error="Must specify embed types to retrieve",
            details={"valid_embed_types": ["latest-wrs", "latest-pbs", "records"]},
        )

    embed_fields = [field.strip() for field in embed.split(",") if field.strip()]
    valid_embed_types = {"latest-wrs", "latest-pbs", "records"}
    invalid_embeds = [field for field in embed_fields if field not in valid_embed_types]

    if invalid_embeds:
        return 400, ErrorResponse(
            error=f"Invalid embed type(s): {', '.join(invalid_embeds)}",
            details={"valid_embed_types": list(valid_embed_types)},
        )

    try:
        response_data = {}

        if "latest-wrs" in embed_fields:
            response_data["latest_wrs"] = get_cached_embed("latest-wrs")

        if "latest-pbs" in embed_fields:
            response_data["latest_pbs"] = get_cached_embed("latest-pbs")

        if "records" in embed_fields:
            response_data["records"] = get_cached_embed("records")

        return 200, response_data
    except Exception as e:
        return 500, ErrorResponse(
            error="Server error!",
            details={"exception": str(e)},
        )


@router.get(
    "/game/{game_id}/categories",
    response={200: list[GameCategoryResponseSchema], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Game Categories with Variables",
    description=dedent(
        """
    Get all categories for a game with their variables and values.
    Optimized for the category selection interface.

    **Supported Parameters:**
    - `game_id` (str): Filter by specific game ID or its slug

    **Examples:**
    - `/website/game/thps4/categories` - Get all THPS4 categories
    - `/website/game/n2680o1p/categories` - Get categories by game ID

    **Note:** This is an aggregation endpoint optimized for the React frontend game page.
    Returns categories with embedded variables and values in a single request.
    """
    ),
    auth=public_auth,
    openapi_extra=GAME_CATEGORIES_GET,
)
@cache_response(key_function=categories_adapter)
def get_game_categories(
    request: HttpRequest,
    game_id: Annotated[str, Query],
) -> tuple[int, list[GameCategoryResponseSchema] | ErrorResponse]:
    """Get categories for a game with variables."""
    if len(game_id) > 15:
        return 400, ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
        )

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return 404, ErrorResponse(
                error="Game not found",
                details=None,
            )

        # Orders categories by the admin-managed `order` field. Categories with order=0
        # fall back to alphabetical sorting at the end of the list.
        categories = (
            Categories.objects.filter(game=game)
            .annotate(
                sort_key=Case(
                    When(order=0, then=Value(999999)),
                    default=F("order"),
                    output_field=IntegerField(),
                )
            )
            .order_by("sort_key", "name")
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related(
                        Prefetch(
                            "variablevalues_set",
                            queryset=VariableValues.objects.annotate(
                                vv_sort_key=Case(
                                    When(order=0, then=Value(999999)),
                                    default=F("order"),
                                    output_field=IntegerField(),
                                )
                            ).order_by("vv_sort_key", "name"),
                        )
                    ),
                )
            )
        )

        categories_data: list[GameCategoryResponseSchema] = []
        for category in categories:
            variables_data: list[VariableWithValuesSchema] = []
            for variable in category.variables_set.all():  # type: ignore
                values_data: list[VariableValueSchema] = [
                    VariableValueSchema(
                        value=val.value,
                        name=val.name,
                        slug=val.slug,
                        appear_on_main=val.appear_on_main,
                        order=val.order,
                        archive=val.archive,
                        rules=val.rules,
                        variable=None,
                    )
                    for val in variable.variablevalues_set.all()
                ]
                variables_data.append(VariableWithValuesSchema(
                    id=variable.id,
                    name=variable.name,
                    slug=variable.slug,
                    scope=variable.scope,
                    archive=variable.archive,
                    values=values_data,
                    game=None,
                    category=None,
                    level=None,
                ))

            categories_data.append(GameCategoryResponseSchema(
                id=category.id,
                name=category.name,
                slug=category.slug,
                type=category.type,
                url=category.url,
                rules=category.rules,
                appear_on_main=category.appear_on_main,
                archive=category.archive,
                variables=variables_data,
            ))

        return 200, categories_data

    except Exception as e:
        return 500, ErrorResponse(
            error="Failed to retrieve game categories",
            details={"exception": str(e)},
        )


@router.get(
    "/game/{game_id}/levels",
    response={200: list[GameLevelResponseSchema], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Game Levels with Variables",
    description=dedent(
        """
    Get all levels for a game with their variables and values.

    **Supported Parameters:**
    - `game_id` (str): Filter by specific game ID or its slug

    **Examples:**
    - `/website/game/thps4/levels` - Get all THPS4 levels
    - `/website/game/n2680o1p/levels` - Get levels by game ID

    **Note:** This is an aggregation endpoint optimized for the React frontend IL page.
    Returns levels with embedded variables and values in a single request.
    """
    ),
    auth=public_auth,
    openapi_extra=GAME_LEVELS_GET,
)
@cache_response(key_function=levels_adapter)
def get_game_levels(
    request: HttpRequest,
    game_id: Annotated[str, Query],
) -> tuple[int, list[GameLevelResponseSchema] | ErrorResponse]:
    """Get levels for a game with variables."""
    if len(game_id) > 15:
        return 400, ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
        )

    try:
        game = Games.objects.filter(
            Q(id__iexact=game_id) | Q(slug__iexact=game_id)
        ).first()
        if not game:
            return 404, ErrorResponse(
                error="Game not found",
                details=None,
            )

        levels = (
            Levels.objects.filter(game=game)
            .annotate(
                sort_key=Case(
                    When(order=0, then=Value(999999)),
                    default=F("order"),
                    output_field=IntegerField(),
                )
            )
            .order_by("sort_key", "name")
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related(
                        Prefetch(
                            "variablevalues_set",
                            queryset=VariableValues.objects.annotate(
                                vv_sort_key=Case(
                                    When(order=0, then=Value(999999)),
                                    default=F("order"),
                                    output_field=IntegerField(),
                                )
                            ).order_by("vv_sort_key", "name"),
                        )
                    ),
                )
            )
        )

        levels_data: list[GameLevelResponseSchema] = []
        for level in levels:
            variables_data = []
            for variable in level.variables_set.all():  # type: ignore
                values_data = [
                    VariableValueSchema(
                        value=val.value,
                        name=val.name,
                        slug=val.slug,
                        appear_on_main=val.appear_on_main,
                        order=val.order,
                        archive=val.archive,
                        rules=val.rules,
                        variable=None,
                    )
                    for val in variable.variablevalues_set.all()
                ]
                variables_data.append(VariableWithValuesSchema(
                    id=variable.id,
                    name=variable.name,
                    slug=variable.slug,
                    scope=variable.scope,
                    archive=variable.archive,
                    values=values_data,
                    game=None,
                    category=None,
                    level=None,
                ))

            levels_data.append(GameLevelResponseSchema(
                id=level.id,
                name=level.name,
                slug=level.slug,
                url=level.url,
                rules=level.rules,
                variables=variables_data,
            ))

        return 200, levels_data

    except Exception as e:
        return 500, ErrorResponse(
            error="Failed to retrieve game levels",
            details={"exception": str(e)},
        )
