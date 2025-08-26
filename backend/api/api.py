from __future__ import annotations

from typing import Any, Dict

from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.errors import ValidationError
from ninja.responses import Response

from .schemas.base import ErrorResponse, ValidationErrorResponse

ninja_api: NinjaAPI = NinjaAPI(
    title="thps.run API",
    version="1.0.0",
    description="""
    This API provides access to the thps.run API and documents its functionality.

    AUTHENTICATION:
    - GET requests are public. No API key is required to access this information.
    - All other HTTP reqeusts will require a valid API key in the X-API-Key header to proceed.
        - If you want an API key, contact ThePackle on the thps.run Discord.

    **Embed System:**
    Most endpoints support an `embed` query parameter to include related data:
    - `?embed=categories,levels` - Include multiple related objects
    - Reduces API calls and improves performance
    - Only valid embeds are accepted per endpoint

    **Error Handling:**
    All errors return consistent JSON with error message and HTTP status code.
    """,
    docs_url="/docs",
    openapi_url="/openapi.json",
    openapi_extra={
        "tags": [
            {
                "name": "Categories",
                "description": "Specific endpoints related to categories.",
            },
            {
                "name": "Games",
                "description": "Specific endpoints related to games.",
            },
            {
                "name": "Levels",
                "description": "Specific endpoints related to levels.",
            },
            {
                "name": "Platforms",
                "description": "Specific endpoints related to platforms.",
            },
            {
                "name": "Players",
                "description": "Specific endpoints related to players.",
            },
            {
                "name": "Runs",
                "description": "Specific endpoints related to runs... Which might be all lol.",
            },
            {
                "name": "Streams",
                "description": "Specific endpoints related to streams appearing in the API.",
            },
            {
                "name": "Variables",
                "description": "Specific endpoints related to variables and variable-value pairs.",
            },
            {
                "name": "Guides",
                "description": "Specific endpoints related to the Guides system of the website.",
            },
            {
                "name": "Website",
                "description": "Specific endpoints related to how the frontend operates.",
            },
            {"name": ""},
        ]
    },
)


# Global exception handlers for consistent error responses
@ninja_api.exception_handler(ValidationError)
def validation_exception_handler(
    request: HttpRequest, exc: ValidationError
) -> Response:
    """
    Handle Pydantic validation errors.

    This provides consistent validation error responses across all endpoints.
    Much cleaner than DRF's validation error handling.

    Args:
        request: The HTTP request that caused the error
        exc: The validation exception from Pydantic

    Returns:
        Standardized validation error response
    """
    return ninja_api.create_response(
        request,
        ValidationErrorResponse(
            error="Request validation failed",
            validation_errors=exc.errors,
            code=422,
        ).dict(),
        status=422,
    )


@ninja_api.exception_handler(Exception)
def global_exception_handler(request: HttpRequest, exc: Exception) -> Response:
    """
    Handle unexpected server errors.

    Provides a consistent error response for unexpected exceptions
    while logging the full error for debugging.

    Args:
        request: The HTTP request that caused the error
        exc: The unexpected exception

    Returns:
        Generic server error response
    """

    return ninja_api.create_response(
        request,
        ErrorResponse(
            error="An unexpected error occurred",
            details=None,
            code=500,
        ).dict(),
        status=500,
    )


@ninja_api.get(
    "/health",
    response=Dict[str, Any],
    summary="API Health Check",
)
def health_check(
    request: HttpRequest,
) -> Dict[str, Any]:
    """A simple API endpoint that returns health information.

    This endpoint returns basic API status and versioning information. This is useful for
    monitoring and ensuring the API is accessible and is responding to requests.

    Returns:
        dict: Returns API health and metadata related to it.

    Example:
        {
            "status": "healthy",
            "version": "1.0.0",
            "message": "Generic health message",
        }
    """
    return {
        "status": "healthy",
        "version": ninja_api.version,
        "message": "thps.run API is operational and is accepting requests.",
    }


from api.routers.guides import guides_router, tags_router
from api.routers.standard import (
    categories_router,
    games_router,
    levels_router,
    platforms_router,
    players_router,
    runs_router,
    streams_router,
    variables_router,
)
from api.routers.website import (
    game_categories_router,
    game_levels_router,
    main_page_router,
)

ninja_api.add_router("/games", games_router, tags=["Games"])
ninja_api.add_router("/categories", categories_router, tags=["Categories"])
ninja_api.add_router("/levels", levels_router, tags=["Levels"])
ninja_api.add_router("/platforms", platforms_router, tags=["Platforms"])
ninja_api.add_router("/players", players_router, tags=["Players"])
ninja_api.add_router("/variables", variables_router, tags=["Variables"])
ninja_api.add_router("/runs", runs_router, tags=["Runs"])
ninja_api.add_router("/streams", streams_router, tags=["Streams"])

ninja_api.add_router("/guides", guides_router, tags=["Guides"])
ninja_api.add_router("/tags", tags_router, tags=["Tags"])

ninja_api.add_router("/website", main_page_router)
ninja_api.add_router("/website", game_categories_router)
ninja_api.add_router("/website", game_levels_router)
