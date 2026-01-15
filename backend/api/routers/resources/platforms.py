from typing import List, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Platforms

from api.docs.platforms import (
    PLATFORMS_ALL,
    PLATFORMS_DELETE,
    PLATFORMS_GET,
    PLATFORMS_POST,
    PLATFORMS_PUT,
)
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse
from api.schemas.platforms import (
    PlatformCreateSchema,
    PlatformSchema,
    PlatformUpdateSchema,
)

router = Router()


@router.get(
    "/{id}",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Get Platform by ID",
    description="""
    Retrieve a single platform by its ID or its slug.

    **Supported Parameters:**
    - `id` (str): Unique ID of the platform being queried.

    **Examples:**
    - `/platforms/8gej2n3z` - Get platform by ID
    - `/platforms/pc` - Get platform by slug
    """,
    auth=public_auth,
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
    - `limit` (Optional[int]): Results per page (default 50, max 100)
    - `offset`(Optional[int]): Results to skip (default 0)

    **Examples:**
    - `/platforms/all` - Get all platforms
    - `/platforms/all?limit=20` - Get first 20 platforms
    - `/platforms/all?limit=10&offset=10` - Get platforms 11-20
    """,
    auth=public_auth,
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

    **Request Body:**
    - `id` (str): Unique ID (usually based on SRC) of the platform being created.
    - `name` (str): Platform name (e.g., "PlayStation 2") being created.
    - `slug` (str): URL-friendly version (e.g., "playstation-2").
    """,
    auth=moderator_auth,
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

    **Supported Parameters:**
    - `id (str): Unique ID (usually based on SRC) of the platform.

    **Request Body:**
    - `name` (Optional[str]): Platform name (e.g., "PlayStation 2") being created.
    - `slug` (Optional[str]): URL-friendly version (e.g., "playstation-2").
    """,
    auth=moderator_auth,
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

    **Supported Parameters:**
    - `id (str): Unique ID (usually based on SRC) of the platform being deleted.
    """,
    auth=admin_auth,
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
