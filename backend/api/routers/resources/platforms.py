from typing import List, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Platforms

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse
from api.schemas.platforms import (
    PlatformCreateSchema,
    PlatformSchema,
    PlatformUpdateSchema,
)

router = Router()

# START OPENAPI DOCUMENTATION #
PLATFORMS_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {"id": "8gej2n3z", "name": "PC", "slug": "pc"}
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Platform could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "8gej2n3z",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Platform ID",
        },
    ],
}

PLATFORMS_POST = {
    "responses": {
        201: {
            "description": "Platform created successfully!",
            "content": {
                "application/json": {
                    "example": {"id": "8gej2n3z", "name": "PC", "slug": "pc"}
                }
            },
        },
        400: {"description": "Invalid request data."},
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
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "PC",
                            "description": "PLATFORM NAME",
                        }
                    },
                },
                "example": {"name": "PC"},
            }
        },
    },
}

PLATFORMS_PUT = {
    "responses": {
        200: {
            "description": "Platform updated successfully!",
            "content": {
                "application/json": {
                    "example": {"id": "8gej2n3z", "name": "PC", "slug": "pc"}
                }
            },
        },
        400: {"description": "Invalid request data."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Platform does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "8gej2n3z",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Platform ID to update",
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
                            "example": "PC",
                            "description": "UPDATED PLATFORM NAME",
                        }
                    },
                },
                "example": {"name": "PC Updated"},
            }
        },
    },
}

PLATFORMS_DELETE = {
    "responses": {
        200: {
            "description": "Platform deleted successfully!",
            "content": {
                "application/json": {
                    "example": {"message": "Platform 'PC' deleted successfully"}
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Platform does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "8gej2n3z",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Platform ID to delete",
        },
    ],
}

PLATFORMS_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {"id": "8gej2n3z", "name": "PC", "slug": "pc"},
                        {"id": "nzelreqy", "name": "PlayStation 2", "slug": "ps2"},
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


@router.get(
    "/{id}",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Get Platform by ID",
    description="""
    Retrieve a single platform by its ID or its slug.

    **Examples:**
    - `/platforms/8gej2n3z` - Get platform by ID
    - `/platforms/pc` - Get platform by slug
    """,
    auth=read_only_auth,
    openapi_extra=PLATFORMS_GET,
)
def get_platform(
    request: HttpRequest,
    id: str,
) -> Union[PlatformSchema, ErrorResponse]:
    if len(id) > 15:
        return ErrorResponse(
            error="ID must be 15 characters or less",
            details=None,
            code=400,
        )

    try:
        platform = Platforms.objects.filter(
            Q(id__iexact=id) | Q(slug__iexact=id)
        ).first()
        if not platform:
            return ErrorResponse(
                error="Platform ID does not exist",
                details=None,
                code=404,
            )

        return PlatformSchema.model_validate(platform)

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve platform",
            details={"exception": str(e)},
            code=500,
        )


@router.get(
    "/all",
    response=Union[List[PlatformSchema], ErrorResponse],
    summary="Get All Platforms",
    description="""
    Retrieve all platforms within the `Platforms` object, ordered by name.

    **Supported Parameters:**
    - `limit`: Results per page (default 50, max 100)
    - `offset`: Results to skip (default 0)

    **Examples:**
    - `/platforms/all` - Get all platforms
    - `/platforms/all?limit=20` - Get first 20 platforms
    - `/platforms/all?limit=10&offset=10` - Get platforms 11-20
    """,
    auth=read_only_auth,
    openapi_extra=PLATFORMS_ALL,
)
def get_all_platforms(
    request: HttpRequest,
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
) -> Union[List[PlatformSchema], ErrorResponse]:
    try:
        platforms = Platforms.objects.all().order_by("name")[offset : offset + limit]
        return [PlatformSchema.model_validate(platform) for platform in platforms]
    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve platforms",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "/",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Create Platform",
    description="""
    Creates a brand new platform.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=PLATFORMS_POST,
)
def create_platform(
    request: HttpRequest,
    platform_data: PlatformCreateSchema,
) -> Union[PlatformSchema, ErrorResponse]:
    try:
        platform = Platforms.objects.create(**platform_data.model_dump())
        return PlatformSchema.model_validate(platform)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create platform",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{id}",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Update Platform",
    description="""
    Updates the platform based on its unique ID.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**
    """,
    auth=api_moderator_check,
    openapi_extra=PLATFORMS_PUT,
)
def update_platform(
    request: HttpRequest,
    id: str,
    platform_data: PlatformUpdateSchema,
) -> Union[PlatformSchema, ErrorResponse]:
    try:
        platform = Platforms.objects.filter(id__iexact=id).first()
        if not platform:
            return ErrorResponse(
                error="Platform does not exist",
                details=None,
                code=404,
            )

        update_data = platform_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(platform, field, value)

        platform.save()
        return PlatformSchema.model_validate(platform)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update platform",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Platform",
    description="""
    Deletes the selected platform based on its ID.

    **REQUIRES ADMIN ACCESS.**
    """,
    auth=api_admin_check,
    openapi_extra=PLATFORMS_DELETE,
)
def delete_platform(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    try:
        platform = Platforms.objects.filter(id__iexact=id).first()
        if not platform:
            return ErrorResponse(
                error="Platform does not exist",
                details=None,
                code=404,
            )

        name = platform.name
        platform.delete()
        return {"message": f"Platform '{name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete platform",
            details={"exception": str(e)},
            code=500,
        )
