from typing import List, Union

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from guides.models import Tags
from ninja import Router

from api.docs.tags import TAGS_ALL, TAGS_DELETE, TAGS_GET, TAGS_POST, TAGS_PUT
from api.permissions import contributor_auth, public_auth
from api.schemas.base import ErrorResponse
from api.schemas.guides import (
    TagCreateSchema,
    TagListSchema,
    TagSchema,
    TagUpdateSchema,
)

router = Router()


@router.get(
    "/all",
    response=List[TagListSchema],
    summary="List All Tags",
    description="""
    Returns a list of all available tags to categorize guides.

    **Examples:**
    - `/tags/all` - Get all tags
    """,
    auth=public_auth,
    openapi_extra=TAGS_ALL,
)
def list_tags(
    request: HttpRequest,
) -> List[TagListSchema]:
    tags = Tags.objects.all().order_by("name")
    return [TagListSchema.model_validate(tag) for tag in tags]


@router.get(
    "/{slug}",
    response=Union[TagSchema, ErrorResponse],
    summary="Get Tag by Slug",
    description="""
    Get a specific tag by its slug.

    **Supported Parameters:**
    - `slug` (str): URL-friendly tag identifier

    **Examples:**
    - `/tags/tricks` - Get the "Tricks" tag
    - `/tags/glitches` - Get the "Glitches" tag
    """,
    auth=public_auth,
    openapi_extra=TAGS_GET,
)
def get_tag(
    request: HttpRequest,
    slug: str,
) -> Union[TagSchema, ErrorResponse]:
    tag = Tags.objects.filter(slug__iexact=slug).first()
    if not tag:
        return ErrorResponse(
            error=f"Tag with slug '{slug}' not found",
            details=None,
            code=404,
        )

    return TagSchema.model_validate(tag)


@router.post(
    "/",
    response=Union[TagSchema, ErrorResponse],
    summary="Create Tag",
    description="""
    Creates a brand new tag for categorizing guides.

    **REQUIRES CONTRIBUTOR ACCESS OR HIGHER.**

    **Request Body:**
    - `name` (str): Name of the tag
    - `description` (str): Description of what this tag represents
    """,
    auth=contributor_auth,
    openapi_extra=TAGS_POST,
)
def create_tag(
    request: HttpRequest,
    data: TagCreateSchema,
) -> Union[TagSchema, ErrorResponse]:
    existing_tag = Tags.objects.filter(name__iexact=data.name).first()
    if existing_tag:
        return ErrorResponse(
            error="Tag With Slug Already Exists",
            details={"slug": existing_tag.slug},
            code=400,
        )

    try:
        tag = Tags.objects.create(
            name=data.name,
            description=data.description,
        )
        return TagSchema.model_validate(tag)
    except Exception as e:
        return ErrorResponse(
            error="Tag Creation Failed",
            details={"exception": {str(e)}},
            code=500,
        )


@router.put(
    "/{slug}",
    response=Union[TagSchema, ErrorResponse],
    summary="Update Tag",
    description="""
    Update an existing tag.

    **REQUIRES CONTRIBUTOR ACCESS OR HIGHER.**

    **Supported Parameters:**
    - `slug` (str): Tag slug to update

    **Request Body:**
    - `name` (Optional[str]): Updated tag name
    - `slug` (Optional[str]): Updated URL-friendly slug
    - `description` (Optional[str]): Updated tag description
    """,
    auth=contributor_auth,
    openapi_extra=TAGS_PUT,
)
def update_tag(
    request: HttpRequest,
    slug: str,
    data: TagUpdateSchema,
) -> Union[TagSchema, ErrorResponse]:
    tag = Tags.objects.filter(slug__iexact=slug).first()
    if not tag:
        return ErrorResponse(
            error=f"Tag with slug '{slug}' not found",
            details=None,
            code=404,
        )

    # After all validations, it will begin to update the tag in the database
    # to then return to the client. Major check here is to ensure that, if the slug
    # is provided, it will ensure that the slug is unique.
    try:
        with transaction.atomic():
            if data.name is not None:
                tag.name = data.name

            if data.slug is not None:
                existing_tag = (
                    Tags.objects.filter(slug__iexact=data.slug)
                    .exclude(pk=tag.pk)
                    .first()
                )
                if existing_tag:
                    return ErrorResponse(
                        error=f"A tag with slug '{data.slug}' already exists",
                        details={"slug": data.slug},
                        code=400,
                    )
                tag.slug = data.slug

            if data.description is not None:
                tag.description = data.description

            tag.save()
            return TagSchema.model_validate(tag)

    except Exception as e:
        return ErrorResponse(
            error=f"Failed to update tag: {str(e)}",
            details=None,
            code=500,
        )


@router.delete(
    "/{slug}",
    response=Union[dict, ErrorResponse],
    summary="Delete Tag",
    description="""
    Delete a tag.

    **REQUIRES CONTRIBUTOR ACCESS OR HIGHER.**

    **Supported Parameters:**
    - `slug` (str): Unique ID or the slug of the tag to remove.
    """,
    auth=contributor_auth,
    openapi_extra=TAGS_DELETE,
)
def delete_tag(
    request: HttpRequest,
    slug: str,
) -> Union[dict, ErrorResponse]:
    tag = Tags.objects.filter(Q(slug__iexact=slug) | Q(pk__iexact=slug)).first()
    if not tag:
        return ErrorResponse(
            error=f"Tag with ID/slug '{slug}' not found",
            details=None,
            code=404,
        )

    try:
        name = tag.name
        tag.delete()
        return {"message": f"Tag '{name}' deleted successfully"}
    except Exception as e:
        return ErrorResponse(
            error=f"Failed to delete tag: {str(e)}",
            details=None,
            code=500,
        )
