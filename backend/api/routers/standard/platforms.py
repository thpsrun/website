from typing import List, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Platforms

from api.auth.api_key import api_key_required, read_only_auth
from api.schemas.base import ErrorResponse
from api.schemas.platforms import (
    PlatformCreateSchema,
    PlatformSchema,
    PlatformUpdateSchema,
)

platforms_router = Router(tags=["Platforms"])


@platforms_router.get(
    "/{id}",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Get Platform by ID",
    description="Retrieve a single platform by its ID.",
    auth=read_only_auth,
)
def get_platform(
    request: HttpRequest,
    id: str,
) -> Union[PlatformSchema, ErrorResponse]:
    """Get a single platform by ID."""
    if len(id) > 15:
        return ErrorResponse(error="ID must be 15 characters or less", code=400)

    try:
        platform = Platforms.objects.filter(id__iexact=id).first()
        if not platform:
            return ErrorResponse(error="Platform ID does not exist", code=404)

        return PlatformSchema.model_validate(platform)

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve platform", details={"exception": str(e)}, code=500
        )


@platforms_router.get(
    "/all",
    response=Union[List[PlatformSchema], ErrorResponse],
    summary="Get All Platforms",
    description="Retrieve all platforms ordered by name.",
    auth=read_only_auth,
)
def get_all_platforms(
    request: HttpRequest,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Union[List[PlatformSchema], ErrorResponse]:
    """Get all platforms with pagination."""
    try:
        platforms = Platforms.objects.all().order_by("name")[offset : offset + limit]
        return [PlatformSchema.model_validate(platform) for platform in platforms]

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve platforms",
            details={"exception": str(e)},
            code=500,
        )


@platforms_router.post(
    "/",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Create Platform",
    auth=api_key_required,
)
def create_platform(
    request: HttpRequest,
    platform_data: PlatformCreateSchema,
) -> Union[PlatformSchema, ErrorResponse]:
    """Create a new platform."""
    try:
        platform = Platforms.objects.create(**platform_data.dict())
        return PlatformSchema.model_validate(platform)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create platform", details={"exception": str(e)}, code=500
        )


@platforms_router.put(
    "/{id}",
    response=Union[PlatformSchema, ErrorResponse],
    summary="Update Platform",
    auth=api_key_required,
)
def update_platform(
    request: HttpRequest,
    id: str,
    platform_data: PlatformUpdateSchema,
) -> Union[PlatformSchema, ErrorResponse]:
    """Update an existing platform."""
    try:
        platform = Platforms.objects.filter(id__iexact=id).first()
        if not platform:
            return ErrorResponse(error="Platform does not exist", code=404)

        update_data = platform_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(platform, field, value)

        platform.save()
        return PlatformSchema.model_validate(platform)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update platform", details={"exception": str(e)}, code=500
        )


@platforms_router.delete(
    "/{id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Platform",
    auth=api_key_required,
)
def delete_platform(
    request: HttpRequest,
    id: str,
) -> Union[dict, ErrorResponse]:
    """Delete a platform."""
    try:
        platform = Platforms.objects.filter(id__iexact=id).first()
        if not platform:
            return ErrorResponse(error="Platform does not exist", code=404)

        name = platform.name
        platform.delete()
        return {"message": f"Platform '{name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete platform", details={"exception": str(e)}, code=500
        )
