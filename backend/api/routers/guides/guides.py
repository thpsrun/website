from typing import Dict, List, Optional, Tuple, Union

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from guides.models import Guides, Tags
from ninja import Query, Router
from ninja.responses import codes_4xx
from srl.models.games import Games

from api.docs.guides import (
    GUIDES_ALL,
    GUIDES_DELETE,
    GUIDES_GET,
    GUIDES_POST,
    GUIDES_PUT,
)
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse, validate_embeds
from api.schemas.games import GameSchema
from api.schemas.guides import (
    GuideCreateSchema,
    GuideListSchema,
    GuideSchema,
    GuideUpdateSchema,
    TagSchema,
)

router = Router()


@router.get(
    "/all",
    response={200: List[GuideListSchema], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="List All Guides",
    description="""
    Gets all guides within the database, with optional querying and embeds.

    **Query Parameters:**
    - `game` (Optional[str]): Filter guides based on the game's slug or ID.
    - `tag` (Optional[str]): Filter guides based on the tag's slug or ID.
    - `embed` (Optional[list]): Comma-separated list of resources to embed.

    **Supported Embeds:**
    - `game`: Includes the metadata of the game the tag belongs to.
    - `tags`: Include metadata of the tags belonging to this guide.
    """,
    auth=public_auth,
    openapi_extra=GUIDES_ALL,
)
def list_guides(
    request: HttpRequest,
    game: Optional[str] = Query(
        None,
        description="Filter by game slug",
    ),
    tag: Optional[str] = Query(
        None,
        description="Filter by tag slug",
    ),
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds (game,tags)",
    ),
) -> Tuple[int, Union[List[GuideListSchema], ErrorResponse]]:
    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
    embed_list = []
    if embed:
        embed_list = [e.strip() for e in embed.split(",")]
        invalid_embeds = validate_embeds("guides", embed_list)
        if invalid_embeds:
            return 400, ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
            )

    queryset = Guides.objects.all()

    # If parameters are fulfilled by the client, this will further
    # drill down what the client is looking for.
    if game:
        queryset = queryset.filter(
            Q(game__slug__iexact=game) | Q(game__id__iexact=game),
        )
    if tag:
        queryset = queryset.filter(
            Q(tags__slug__iexact=tag) | Q(tags__id__iexact=tag),
        )

    # If embeds are added, this will append further information
    # based on what is being requested.
    if "game" in embed_list:
        queryset = queryset.select_related("game")
    if "tags" in embed_list:
        queryset = queryset.prefetch_related("tags")

    # Validates the guides in the queryset before returning it
    # to the client.
    result = []
    for guide in queryset:
        guide_data = GuideListSchema.model_validate(guide)

        if "game" in embed_list and guide.game:
            guide_data.game = GameSchema.model_validate(guide.game)
        if "tags" in embed_list:
            guide_data.tags = [
                TagSchema.model_validate(tag) for tag in guide.tags.all()
            ]

        result.append(guide_data)

    return 200, result


@router.get(
    "/{slug}",
    response={200: GuideSchema, codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Get Guide by Slug",
    description="""
    Get a specific guide by its slug.

    **Supported Parameters:**
    - `slug` (str): Simplified, URL friendly name of the guide.
    - `embed` (Optional[list]): Comma-separated list of resources to embed.

    **Supported Embeds:**
    - `game`: Includes the metadata of the game the tag belongs to.
    - `tags`: Include metadata of the tags belonging to this guide.
    """,
    auth=public_auth,
    openapi_extra=GUIDES_GET,
)
def get_guide(
    request: HttpRequest,
    slug: str,
    embed: Optional[str] = Query(
        None,
        description="Comma-separated embeds (game,tags)",
    ),
) -> Tuple[int, Union[GuideSchema, ErrorResponse]]:
    # Checks to see what embeds are being used versus what is allowed
    # via this endpoint. It will return an error to the client if they
    # have an embed type not supported.
    embed_list = []
    if embed:
        embed_list = [e.strip() for e in embed.split(",")]
        invalid_embeds = validate_embeds("guides", embed_list)
        if invalid_embeds:
            return 400, ErrorResponse(
                error=f"Invalid embed(s): {', '.join(invalid_embeds)}",
                details=None,
            )

    # Will check to see if a query exists then related/prefetch the embeds
    # provided for more information (if they are declared). It will then
    # do a quick check to see if the Guide exists, if not it will throw a 404.
    queryset = Guides.objects.filter(slug__iexact=slug)
    if "game" in embed_list:
        queryset = queryset.select_related("game")
    if "tags" in embed_list:
        queryset = queryset.prefetch_related("tags")

    guide = queryset.first()
    if not guide:
        return 404, ErrorResponse(
            error=f"Guide with slug '{slug}' not found",
            details=None,
        )

    return 200, GuideSchema.model_validate(guide)


@router.post(
    "/",
    response={200: GuideSchema, codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Create New Guide",
    description="""
    Creates a brand new guide.

    **REQUIRES CONTRIBUTOR ACCESS OR HIGHER.**

    **Request Body:**
    - `title` (str): Name of the guide.
    - `game_id` (str): Unique game ID or slug of the game this is associated with.
    - `tag_ids` (Optional[list]): List of tag IDs or their slug.
    - `short_description` (str): Brief description of the guide (limit 500 characters).
    - `content` (str): Full guide content (markdown supported).
    """,
    auth=moderator_auth,
    openapi_extra=GUIDES_POST,
)
def create_guide(
    request: HttpRequest,
    data: GuideCreateSchema,
) -> Tuple[int, Union[GuideSchema, ErrorResponse]]:
    try:
        game = Games.objects.get(id=data.game_id)
    except Games.DoesNotExist:
        return 400, ErrorResponse(
            error="Game ID Doesn't Exist",
            details={"games": {data.game_id}},
        )

    # Bulk checking all tags specified by the user versus what is currently
    # within the `Tags` database. This endpoint does not auto-create them,
    # so it will show an error if one fails.
    if data.tag_ids:
        existing_tags = Tags.objects.filter(
            Q(id__in=data.tag_ids) | Q(slug__in=data.tag_ids)
        )

        found_identifiers = set(existing_tags.values_list("id", flat=True)).union(
            existing_tags.values_list("slug", flat=True)
        )

        provided_tags = set(data.tag_ids)
        missing_tags = provided_tags - found_identifiers

        if missing_tags:
            return 400, ErrorResponse(
                error="Tags not found",
                details={"missing_tags": list(missing_tags)},
            )

    # Will attempt to create the guide based on the payload provided by the client.
    # If an error occurs with creation at any point, it will fail and throw a 500.
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
            guide_data.game = GameSchema.model_validate(guide.game)
            guide_data.tags = [
                TagSchema.model_validate(tag) for tag in guide.tags.all()
            ]

            return 200, guide_data
    except Exception as e:
        return 500, ErrorResponse(
            error="Guide Creation Failed",
            details={"exception": {str(e)}},
        )


@router.put(
    "/{slug}",
    response={200: GuideSchema, codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Update Guide",
    description="""
    Modifies an existing guide.

    **REQUIRES CONTRIBUTOR ACCESS OR HIGHER.**

    **Request Body:**
    - `title` (Optional[str]): Name of the guide.
    - `game_id` (Optional[str]): Unique game ID or slug of the game this is associated with.
    - `tag_ids` (Optional[list]): List of tag IDs or their slug.
    - `short_description` (Optional[str]): Brief description of the guide (limit 500 characters).
    - `content` (Optional[str]): Full guide content (markdown supported).
    """,
    auth=moderator_auth,
    openapi_extra=GUIDES_PUT,
)
def update_guide(
    request: HttpRequest,
    slug: str,
    data: GuideUpdateSchema,
) -> Tuple[int, Union[GuideSchema, ErrorResponse]]:
    guide = Guides.objects.filter(slug__iexact=slug).first()
    if not guide:
        return 404, ErrorResponse(
            error=f"Guide with slug '{slug}' not found",
            details=None,
        )

    if data.game_id:
        try:
            Games.objects.get(id=data.game_id)
        except Games.DoesNotExist:
            return 400, ErrorResponse(
                error=f"Game with ID '{data.game_id}' does not exist",
                details=None,
            )

    # Bulk checking all tags specified by the user versus what is currently
    # within the `Tags` database. This endpoint does not auto-create them,
    # so it will show an error if one fails.
    if data.tag_ids is not None:
        existing_tags = Tags.objects.filter(
            Q(id__in=data.tag_ids) | Q(slug__in=data.tag_ids)
        )

        found_identifiers = set(existing_tags.values_list("id", flat=True)).union(
            existing_tags.values_list("slug", flat=True)
        )

        provided_tags = set(data.tag_ids)
        missing_tags = provided_tags - found_identifiers

        if missing_tags:
            return 400, ErrorResponse(
                error="Tags not found",
                details={"missing_tags": list(missing_tags)},
            )

    # After all validations, it will begin to update the guide in the database
    # to then return to the client. Major check here is to ensure that, if the slug
    # is provided, it will ensure that the slug is unique.
    try:
        with transaction.atomic():
            if data.title is not None:
                guide.title = data.title

            if data.slug is not None:
                existing_guide = (
                    Guides.objects.filter(slug__iexact=data.slug)
                    .exclude(id=guide.pk)
                    .first()
                )
                if existing_guide:
                    return 400, ErrorResponse(
                        error="Guide With Slug Already Exists",
                        details={"slug": data.slug},
                    )
                guide.slug = data.slug

            if data.game_id:
                guide.game = Games.objects.get(id=data.game_id)
            if data.short_description is not None:
                guide.short_description = data.short_description
            if data.content is not None:
                guide.content = data.content

            guide.save()

            if data.tag_ids is not None:
                guide.tags.set(data.tag_ids)

            return 200, GuideSchema.model_validate(guide)
    except Exception as e:
        return 500, ErrorResponse(
            error="Guide Update Failed",
            details={"exception": {str(e)}},
        )


@router.delete(
    "/{slug}",
    response={200: Dict[str, str], codes_4xx: ErrorResponse, 500: ErrorResponse},
    summary="Delete Guide",
    description="""
    Deletes an existing guide.

    **REQUIRES ADMIN ACCESS OR HIGHER.**

    **Supported Parameters:**
    - `slug` (str): Simplified, URL friendly name of the guide.
    """,
    auth=admin_auth,
    openapi_extra=GUIDES_DELETE,
)
def delete_guide(
    request: HttpRequest,
    slug: str,
) -> Tuple[int, Union[Dict[str, str], ErrorResponse]]:
    guide = Guides.objects.filter(slug__iexact=slug).first()
    if not guide:
        return 404, ErrorResponse(
            error=f"Guide with slug '{slug}' not found",
            details=None,
        )

    try:
        title = guide.title
        guide.delete()
        return 200, {"message": f"Guide '{title} deleted successfully."}
    except Exception as e:
        return 500, ErrorResponse(
            error="Guide Delete Failed",
            details={"exception": {str(e)}},
        )
