from __future__ import annotations

from typing import List, Tuple, Union

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from guides.models import Tags
from ninja import Router

from api.schemas.base import ErrorResponse
from api.schemas.guides import (
    TagCreateSchema,
    TagListSchema,
    TagSchema,
    TagUpdateSchema,
)

tags_router: Router = Router()


@tags_router.get(
    "/all",
    response=List[TagListSchema],
    summary="List All Tags",
    description="Retrieve all guide tags",
)
def list_tags(request: HttpRequest) -> List[TagListSchema]:
    """
    Get all guide tags.

    Returns a list of all available tags for categorizing guides.
    """
    tags = Tags.objects.all()  # type: ignore[misc]
    return [TagListSchema.from_orm(tag) for tag in tags]


@tags_router.get(
    "/{slug}",
    response=TagSchema,
    summary="Get Tag by Slug",
    description="Retrieve a specific tag by its slug",
)
def get_tag(request: HttpRequest, slug: str) -> TagSchema:
    """
    Get a specific tag by slug.

    Path Parameters:
    - slug: Tag slug (URL-friendly identifier)
    """
    tag: Tags = get_object_or_404(Tags, slug=slug)
    return TagSchema.from_orm(tag)


@tags_router.post(
    "/",
    response=TagSchema,
    summary="Create Tag",
    description="Create a new tag (requires contributor role or higher)",
)
def create_tag(request: HttpRequest, data: TagCreateSchema) -> Union[TagSchema, Tuple[int, ErrorResponse]]:
    """
    Create a new tag.

    Requires contributor authentication or higher.

    Request Body:
    - name: Tag name
    - description: Tag description

    Returns the created tag.
    """
    try:
        tag: Tags = Tags.objects.create(
            name=data.name,
            description=data.description,
        )
        return TagSchema.from_orm(tag)
    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to create tag: {str(e)}",
            code=500,
        )


@tags_router.put(
    "/{slug}",
    response=TagSchema,
    summary="Update Tag",
    description="Update an existing tag (requires contributor role or higher)",
)
def update_tag(request: HttpRequest, slug: str, data: TagUpdateSchema) -> Union[TagSchema, Tuple[int, ErrorResponse]]:
    """
    Update an existing tag.

    Requires contributor authentication or higher.

    Path Parameters:
    - slug: Tag slug to update

    Request Body (all fields optional):
    - name: Updated name
    - description: Updated description

    Returns the updated tag.
    """
    tag: Tags = get_object_or_404(Tags, slug=slug)

    try:
        # Update fields
        if data.name is not None:
            tag.name = data.name
            tag.slug = ""  # Reset slug to trigger regeneration
        if data.description is not None:
            tag.description = data.description

        tag.save()
        return TagSchema.from_orm(tag)

    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to update tag: {str(e)}",
            code=500,
        )


@tags_router.delete(
    "/{slug}",
    response={204: None},
    summary="Delete Tag",
    description="Delete a tag (requires contributor role or higher)",
)
def delete_tag(request: HttpRequest, slug: str) -> Union[Tuple[int, None], Tuple[int, ErrorResponse]]:
    """
    Delete a tag.

    Requires contributor authentication or higher.

    Path Parameters:
    - slug: Tag slug to delete

    Returns 204 No Content on success.
    """
    tag: Tags = get_object_or_404(Tags, slug=slug)

    try:
        tag.delete()
        return 204, None
    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to delete tag: {str(e)}",
            code=500,
        )
