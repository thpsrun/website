from typing import List, Optional, Union

from django.db import transaction
from django.db.models import Q
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

router = Router()

# OpenAPI documentation
GUIDES_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "1234",
                            "title": "THPS4 Guide",
                            "slug": "thps4-guide",
                            "game": "thps4",
                            "tags": ["tricks", "beginner", "TAS"],
                            "short_description": "Learn the basics of THPS4!",
                            "created_at": "2025-08-15T10:30:00Z",
                            "updated_at": "2025-08-15T10:30:00Z",
                        }
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Guide could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game",
            "in": "query",
            "example": "thps34",
            "schema": {"pattern": "^[a-z0-9-]+$"},
        },
        {
            "name": "tags",
            "in": "query",
            "example": "tricks",
            "schema": {"pattern": "^[a-z0-9-]+$"},
        },
        {
            "name": "embed",
            "in": "embed",
            "example": "game",
            "schema": {"pattern": "^[a-z0-9-]+$"},
        },
    ],
}

GUIDES_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1234",
                        "title": "THPS4 Guide",
                        "slug": "thps4-guide",
                        "game": "thps4",
                        "tags": ["tricks", "beginner", "TAS"],
                        "short_description": "Learn the basics in THPS4!",
                        "content": "# Basics\n\nBlah blah blah...",
                        "created_at": "2025-08-15T10:30:00Z",
                        "updated_at": "2025-08-15T10:30:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Guide could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "embed",
            "in": "embed",
            "example": "game",
            "schema": {"pattern": "^[a-z0-9-]+$"},
        },
    ],
}

GUIDES_POST = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1234",
                        "title": "THPS4 Guide",
                        "slug": "thps4-guide",
                        "game": "thps4",
                        "tags": ["tricks", "beginner", "TAS"],
                        "short_description": "Learn the basics in THPS4!",
                        "content": "# Basics\n\nBlah blah blah...",
                        "created_at": "2025-08-15T10:30:00Z",
                        "updated_at": "2025-08-15T10:30:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "content": {
            "application/json": {
                "example": {
                    "title": "THPS4 Guide",
                    "slug": "thps4-guide",
                    "game": "thps4",
                    "tags": ["tricks", "beginner", "TAS"],
                    "short_description": "Learn the basics in THPS4!",
                    "content": "# Basics\n\nBlah blah blah...",
                }
            }
        }
    },
}

GUIDES_PUT = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1234",
                        "title": "THPS4 Guide",
                        "slug": "thps4-guide",
                        "game": "thps4",
                        "tags": ["tricks", "beginner", "TAS"],
                        "short_description": "Learn the advanced in THPS4!",
                        "content": "# Advanced\n\nBlah blah blah...",
                        "created_at": "2025-08-15T10:30:00Z",
                        "updated_at": "2025-08-15T13:30:00Z",
                    }
                }
            },
        },
        404: {"description": "Guide does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "content": {
            "application/json": {
                "example": {
                    "title": "THPS4 Guide",
                    "slug": "thps4-guide",
                    "game": "thps4",
                    "tags": ["tricks", "beginner", "TAS"],
                    "short_description": "Learn the advanced tricks in THPS4!",
                    "content": "# Advanced\n\nBlah blah blah...",
                }
            }
        }
    },
}


@router.get(
    "/all",
    response=Union[List[GuideListSchema], ErrorResponse],
    summary="List All Guides",
    description="""
    Gets all guides within the database, with optional querying and embeds.

    Embed Parameters:
    - `embed`: Include all related data within the query (game, tags).

    Query Parameters:
    - `game` (str): Filter guides based on the game's slug or ID.
    - `tag` (str): Filter guides based on the tag's slug or ID.
    """,
    openapi_extra=GUIDES_ALL,
)
def list_guides(
    request: HttpRequest,
    game: Optional[str] = Query(None, description="Filter by game slug"),
    tag: Optional[str] = Query(None, description="Filter by tag slug"),
    embed: Optional[str] = Query(
        None, description="Comma-separated embeds (game,tags)"
    ),
) -> List[GuideListSchema]:
    embed_list = []
    if embed:
        embed_list = [e.strip() for e in embed.split(",")]
        invalid_embeds = validate_embeds("guides", embed_list)
        if invalid_embeds:
            return ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
                code=400,
            )

    queryset = Guides.objects.all()

    if game:
        queryset = queryset.filter(
            Q(game__slug__iexact=game) | Q(game__id__iexact=game),
        )
    if tag:
        queryset = queryset.filter(
            Q(tags__slug__iexact=tag) | Q(tags__id__iexact=game),
        )

    if "game" in embed_list:
        queryset = queryset.select_related("game")
    if "tags" in embed_list:
        queryset = queryset.prefetch_related("tags")

    guides = list(queryset.distinct())

    result = []
    for guide in guides:
        guide_data = GuideListSchema.model_validate(guide)

        if "game" in embed_list:
            guide_data.game = guide.game
        if "tags" in embed_list:
            guide_data.tags = list(guide.tags.all())

        result.append(guide_data)

    return result


@router.get(
    "/{slug}",
    response=GuideSchema,
    summary="Get Guide by Slug",
    description="""
    Get a specific guide by its slug.

    Parameters:
    - slug (str): Simplified, URL friendly name of the guide.

    Query Parameters:
    - embed (list): Include all related data within the query (game, tags).
    """,
    openapi_extra=GUIDES_GET,
)
def get_guide(
    request: HttpRequest,
    slug: str,
    embed: Optional[str] = Query(
        None, description="Comma-separated embeds (game,tags)"
    ),
) -> GuideSchema:
    embed_list = []
    if embed:
        embed_list = [e.strip() for e in embed.split(",")]
        invalid_embeds = validate_embeds("guides", embed_list)
        if invalid_embeds:
            return 400, ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                code=400,
            )

    queryset = Guides.objects.all()
    if "game" in embed_list:
        queryset = queryset.select_related("game")
    if "tags" in embed_list:
        queryset = queryset.prefetch_related("tags")

    guide = get_object_or_404(queryset, slug=slug)

    guide_data = GuideSchema.model_validate(guide)

    if "game" in embed_list:
        guide_data.game = guide.game
    if "tags" in embed_list:
        guide_data.tags = list(guide.tags.all())

    return guide_data


@router.post(
    "/",
    response=GuideSchema,
    summary="Create New Guide",
    description="""
    Creates a brand new guide.

    REQUIRES CONTRIBUTOR ACCESS OR HIGHER.

    Request Body:
    - title (str): Name of the guide.
    - game_id (str): Unique game ID or slug of the game this is associated with.
    - tag_ids [Optional] (list): List of tag IDs or their slug.
    - short_description (str): Brief description of the guide (limit 500 characters).
    - content (str): Full guide content (markdown supported).
    """,
    openapi_extra=GUIDES_POST,
)
def create_guide(
    request: HttpRequest,
    data: GuideCreateSchema,
) -> GuideSchema:
    try:
        game = Games.objects.get(id=data.game_id)
    except Games.DoesNotExist:
        return 400, ErrorResponse(
            error=f"Game with ID '{data.game_id}' does not exist",
            code=400,
        )

    if data.tag_ids:
        existing_tags = Tags.objects.filter(
            Q(id__in=data.tag_ids) | Q(slug__in=data.tag_ids),
        )
        if len(existing_tags) != len(data.tag_ids):
            missing_ids = set(data.tag_ids) - set(
                existing_tags.values_list("id", flat=True)
            )
            return 400, ErrorResponse(
                error=f"Tags with IDs/slugs {list(missing_ids)} do not exist",
                code=400,
            )

    try:
        with transaction.atomic():
            guide = Guides.objects.create(
                title=data.title,
                game=game,
                short_description=data.short_description,
                content=data.content,
            )

            if data.tag_ids:
                guide.tags.set(data.tag_ids)

            guide_data = GuideSchema.model_validate(guide)
            guide_data.game = guide.game
            guide_data.tags = list(guide.tags.all())

            return guide_data
    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to create guide: {str(e)}",
            code=500,
        )


@router.put(
    "/{slug}",
    response=GuideSchema,
    summary="Update Guide",
    description="""
    Modifies an existing guide.

    REQUIRES CONTRIBUTOR ACCESS OR HIGHER.

    Request Body:
    - title (str): Name of the guide.
    - game_id (str): Unique game ID or slug of the game this is associated with.
    - tag_ids [Optional] (list): List of tag IDs or their slug.
    - short_description (str): Brief description of the guide (limit 500 characters).
    - content (str): Full guide content (markdown supported).
    """,
    openapi_extra=GUIDES_PUT,
)
def update_guide(
    request: HttpRequest,
    slug: str,
    data: GuideUpdateSchema,
) -> GuideSchema:
    guide = get_object_or_404(Guides, slug=slug)

    if data.game_id:
        try:
            Games.objects.get(id=data.game_id)
        except Games.DoesNotExist:
            return 400, ErrorResponse(
                error=f"Game with ID '{data.game_id}' does not exist",
                code=400,
            )

    if data.tag_ids is not None:
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
            if data.title is not None:
                guide.title = data.title
                guide.slug = ""
            if data.game_id:
                guide.game = Games.objects.get(id=data.game_id)
            if data.short_description is not None:
                guide.short_description = data.short_description
            if data.content is not None:
                guide.content = data.content

            guide.save()

            if data.tag_ids is not None:
                guide.tags.set(data.tag_ids)

            guide_data = GuideSchema.model_validate(guide)
            guide_data.game = guide.game
            guide_data.tags = list(guide.tags.all())

            return guide_data

    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to update guide: {str(e)}",
            code=500,
        )


@router.delete(
    "/{slug}",
    response={204: None},
    summary="Delete Guide",
    description="""
    Deletes an existing guide.

    REQUIRES CONTRIBUTOR ACCESS OR HIGHER.

    Parameters:
    - slug (str): Simplified, URL friendly name of the guide.
    """,
)
def delete_guide(
    request: HttpRequest,
    slug: str,
):
    guide = get_object_or_404(Guides, slug=slug)

    try:
        guide.delete()
        return 204, None
    except Exception as e:
        return 500, ErrorResponse(
            error=f"Failed to delete guide: {str(e)}",
            code=500,
        )
