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

router: Router = Router()


@router.get(
    "/all",
    response=List[TagListSchema],
    summary="List All Tags",
    description="""
    Returns a list of all available tags to categorize the guides.
    """,
)
def list_tags(
    request: HttpRequest,
) -> List[TagListSchema]:
    tags = Tags.objects.all()
    return [TagListSchema.model_validate(tag) for tag in tags]


@router.get(
    "/{slug}",
    response=TagSchema,
    summary="Get Tag by Slug",
    description="""
    Get a specific tag by its slug.

    Parameters:
    - slug (str): Simplified, URL friendly name of the tag.
    """,
)
def get_tag(
    request: HttpRequest,
    slug: str,
) -> TagSchema:
    tag: Tags = get_object_or_404(Tags, slug=slug)
    return TagSchema.model_validate(tag)


@router.post(
    "/",
    response=TagSchema,
    summary="Create Tag",
    description="""
    Creates a brand new tag.

    REQUIRES CONTRIBUTOR ACCESS OR HIGHER.

    Request Body:
    - name (str): Name of the tag.
    - description (str): Description of the tag.
    """,
)
def create_tag(
    request: HttpRequest,
    data: TagCreateSchema,
) -> Union[TagSchema, Tuple[int, ErrorResponse]]:
    try:
        tag: Tags = Tags.objects.create(
            name=data.name,
            description=data.description,
        )
        return TagSchema.model_validate(tag)
    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to create tag: {str(e)}",
            code=500,
        )


@router.put(
    "/{slug}",
    response=TagSchema,
    summary="Update Tag",
    description="Update an existing tag (requires contributor role or higher)",
    tags=["Privileged"],
)
def update_tag(
    request: HttpRequest, slug: str, data: TagUpdateSchema
) -> Union[TagSchema, Tuple[int, ErrorResponse]]:
    """
    Update an existing tag.

    REQUIRES CONTRIBUTOR ACCESS OR HIGHER.

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


@router.delete(
    "/{slug}",
    response={204: None},
    summary="Delete Tag",
    description="Delete a tag (requires contributor role or higher)",
)
def delete_tag(
    request: HttpRequest, slug: str
) -> Union[Tuple[int, None], Tuple[int, ErrorResponse]]:
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
