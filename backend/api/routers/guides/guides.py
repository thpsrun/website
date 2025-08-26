from typing import List, Optional

from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from guides.models import Guides, Tags
from ninja import Query, Router
from srl.models.games import Games

from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.guides import (
    GuideCreateSchema,
    GuideListSchema,
    GuideSchema,
    GuideUpdateSchema,
)

guides_router = Router()


@guides_router.get(
    "/all",
    response=List[GuideListSchema],
    summary="List All Guides",
    description="Retrieve all guides with optional filtering by game and tag",
)
def list_guides(
    request: HttpRequest,
    game: Optional[str] = Query(None, description="Filter by game slug"),
    tag: Optional[str] = Query(None, description="Filter by tag slug"),
    embed: Optional[str] = Query(
        None, description="Comma-separated embeds (game,tags)"
    ),
):
    """
    Get all guides with optional filtering and embeds.

    Query Parameters:
    - game: Filter guides by game slug
    - tag: Filter guides by tag slug
    - embed: Include related data (game, tags)

    Examples:
    - /guides/all - All guides
    - /guides/all?game=thps4 - Guides for THPS4
    - /guides/all?tag=tricks - Guides tagged with 'tricks'
    - /guides/all?embed=game,tags - Include game and tag data
    """
    # Validate embeds
    embed_list = []
    if embed:
        embed_list = [e.strip() for e in embed.split(",")]
        invalid_embeds = validate_embeds("guides", embed_list)
        if invalid_embeds:
            return 400, ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                code=400,
            )

    # Base query
    queryset = Guides.objects.all()

    # Apply filters
    if game:
        queryset = queryset.filter(game__slug=game)
    if tag:
        queryset = queryset.filter(tags__slug=tag)

    # Apply embeds
    if "game" in embed_list:
        queryset = queryset.select_related("game")
    if "tags" in embed_list:
        queryset = queryset.prefetch_related("tags")

    guides = list(queryset.distinct())

    # Convert to schemas
    result = []
    for guide in guides:
        guide_data = GuideListSchema.from_orm(guide)

        # Handle embeds
        if "game" in embed_list:
            guide_data.game = guide.game
        if "tags" in embed_list:
            guide_data.tags = list(guide.tags.all())

        result.append(guide_data)

    return result


@guides_router.get(
    "/{slug}",
    response=GuideSchema,
    summary="Get Guide by Slug",
    description="Retrieve a specific guide by its slug with optional embeds",
)
def get_guide(
    request: HttpRequest,
    slug: str,
    embed: Optional[str] = Query(
        None, description="Comma-separated embeds (game,tags)"
    ),
):
    """
    Get a specific guide by slug.

    Path Parameters:
    - slug: Guide slug (URL-friendly identifier)

    Query Parameters:
    - embed: Include related data (game, tags)

    Examples:
    - /guides/thps4-skitchin-guide - Get guide
    - /guides/thps4-skitchin-guide?embed=game,tags - Include related data
    """
    # Validate embeds
    embed_list = []
    if embed:
        embed_list = [e.strip() for e in embed.split(",")]
        invalid_embeds = validate_embeds("guides", embed_list)
        if invalid_embeds:
            return 400, ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                code=400,
            )

    # Build query with embeds
    queryset = Guides.objects
    if "game" in embed_list:
        queryset = queryset.select_related("game")
    if "tags" in embed_list:
        queryset = queryset.prefetch_related("tags")

    guide = get_object_or_404(queryset, slug=slug)

    # Convert to schema
    guide_data = GuideSchema.from_orm(guide)

    # Handle embeds
    if "game" in embed_list:
        guide_data.game = guide.game
    if "tags" in embed_list:
        guide_data.tags = list(guide.tags.all())

    return guide_data


@guides_router.post(
    "/",
    response=GuideSchema,
    summary="Create Guide",
    description="Create a new guide (requires contributor role or higher)",
)
def create_guide(request: HttpRequest, data: GuideCreateSchema):
    """
    Create a new guide.

    Requires contributor authentication or higher.

    Request Body:
    - title: Guide title
    - game_id: Associated game ID
    - tag_ids: List of tag IDs (optional)
    - short_description: Brief description
    - content: Full guide content (Markdown supported)

    Returns the created guide with all data.
    """
    # Validate game exists
    try:
        game = Games.objects.get(id=data.game_id)
    except Games.DoesNotExist:
        return 400, ErrorResponse(
            error=f"Game with ID '{data.game_id}' does not exist",
            code=400,
        )

    # Validate tags exist
    if data.tag_ids:
        existing_tags = Tags.objects.filter(id__in=data.tag_ids)
        if len(existing_tags) != len(data.tag_ids):
            missing_ids = set(data.tag_ids) - set(
                existing_tags.values_list("id", flat=True)
            )
            return 400, ErrorResponse(
                error=f"Tags with IDs {list(missing_ids)} do not exist",
                code=400,
            )

    try:
        with transaction.atomic():
            # Create guide
            guide = Guides.objects.create(
                title=data.title,
                game=game,
                short_description=data.short_description,
                content=data.content,
            )

            # Add tags if provided
            if data.tag_ids:
                guide.tags.set(data.tag_ids)

            # Return with embeds
            guide_data = GuideSchema.from_orm(guide)
            guide_data.game = guide.game
            guide_data.tags = list(guide.tags.all())

            return guide_data

    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to create guide: {str(e)}",
            code=500,
        )


@guides_router.put(
    "/{slug}",
    response=GuideSchema,
    summary="Update Guide",
    description="Update an existing guide (requires contributor role or higher)",
)
def update_guide(request: HttpRequest, slug: str, data: GuideUpdateSchema):
    """
    Update an existing guide.

    Requires contributor authentication or higher.

    Path Parameters:
    - slug: Guide slug to update

    Request Body (all fields optional):
    - title: Updated title
    - game_id: Updated game ID
    - tag_ids: Updated tag IDs
    - short_description: Updated description
    - content: Updated content

    Returns the updated guide with all data.
    """
    guide = get_object_or_404(Guides, slug=slug)

    # Validate game if provided
    if data.game_id:
        try:
            Games.objects.get(id=data.game_id)
        except Games.DoesNotExist:
            return 400, ErrorResponse(
                error=f"Game with ID '{data.game_id}' does not exist",
                code=400,
            )

    # Validate tags if provided
    if data.tag_ids is not None:
        if data.tag_ids:  # Only validate if list is not empty
            existing_tags = Tags.objects.filter(id__in=data.tag_ids)
            if len(existing_tags) != len(data.tag_ids):
                missing_ids = set(data.tag_ids) - set(
                    existing_tags.values_list("id", flat=True)
                )
                return 400, ErrorResponse(
                    error=f"Tags with IDs {list(missing_ids)} do not exist",
                    code=400,
                )

    try:
        with transaction.atomic():
            # Update fields
            if data.title is not None:
                guide.title = data.title
                guide.slug = ""  # Reset slug to trigger regeneration
            if data.game_id:
                guide.game = Games.objects.get(id=data.game_id)
            if data.short_description is not None:
                guide.short_description = data.short_description
            if data.content is not None:
                guide.content = data.content

            guide.save()

            # Update tags if provided
            if data.tag_ids is not None:
                guide.tags.set(data.tag_ids)

            # Return with embeds
            guide_data = GuideSchema.from_orm(guide)
            guide_data.game = guide.game
            guide_data.tags = list(guide.tags.all())

            return guide_data

    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to update guide: {str(e)}",
            code=500,
        )


@guides_router.delete(
    "/{slug}",
    response={204: None},
    summary="Delete Guide",
    description="Delete a guide (requires contributor role or higher)",
)
def delete_guide(request: HttpRequest, slug: str):
    """
    Delete a guide.

    Requires contributor authentication or higher.

    Path Parameters:
    - slug: Guide slug to delete

    Returns 204 No Content on success.
    """
    guide = get_object_or_404(Guides, slug=slug)

    try:
        guide.delete()
        return 204, None
    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to delete guide: {str(e)}",
            code=500,
        )
