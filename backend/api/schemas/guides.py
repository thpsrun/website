from datetime import datetime
from typing import List, Optional

from pydantic import Field

from api.schemas.base import BaseEmbedSchema, SlugMixin, TimestampMixin
from api.schemas.games import GameSchema


class TagSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Tag` data without embeds.

    Attributes:
        name (str): Tag name (e.g., "Tricks", "Glitches").
        slug (str): URL-friendly version of name.
        description (str): Description of what this tag represents.
    """

    description: str = Field(..., description="Description of the tag")


class GuideSchema(SlugMixin, TimestampMixin, BaseEmbedSchema):
    """Base schema for `Guide` data without embeds.

    Attributes:
        title (str): Guide title.
        slug (str): URL-friendly version of title.
        short_description (str): Brief description of guide content.
        content (str): Full guide content (Markdown supported).
        created_at (Optional[datetime]): When guide was created.
        updated_at (Optional[datetime]): When guide was last updated.
        game (Optional[GameSchema]): Associated game - included with ?embed=game.
        tags (Optional[List[TagSchema]]): Associated tags - included with ?embed=tags.
    """

    title: str = Field(..., description="Guide title")
    short_description: str = Field(
        ..., description="Brief description of guide content"
    )
    content: str = Field(..., description="Full guide content (supports Markdown)")

    game: Optional[GameSchema] = Field(
        default=None, description="Associated game"
    )
    tags: Optional[List[TagSchema]] = Field(
        default=None, description="Guide tags"
    )


class GuideCreateSchema(BaseEmbedSchema):
    """Schema for creating new guides.

    Attributes:
        title (str): Guide title.
        game_id (str): Associated game ID.
        tag_ids (Optional[List[int]]): List of tag IDs to associate with guide.
        short_description (str): Brief description.
        content (str): Full guide content.
    """

    title: str = Field(..., min_length=1, max_length=200, description="Guide title")
    game_id: str = Field(..., description="Associated game ID")
    tag_ids: Optional[List[int]] = Field(
        default=[], description="List of tag IDs to associate with guide"
    )
    short_description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Brief description of guide content",
    )
    content: str = Field(
        ..., min_length=1, description="Full guide content (Markdown supported)"
    )


class GuideUpdateSchema(BaseEmbedSchema):
    """Schema for updating existing guides.

    Attributes:
        title (Optional[str]): Updated guide title.
        slug (Optional[str]): Updated URL-friendly slug.
        game_id (Optional[str]): Updated associated game ID.
        tag_ids (Optional[List[int]]): Updated list of tag IDs.
        short_description (Optional[str]): Updated brief description.
        content (Optional[str]): Updated full content.
    """

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=200, description="Updated guide title"
    )
    slug: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated URL-friendly slug",
    )
    game_id: Optional[str] = Field(
        default=None, description="Updated associated game ID"
    )
    tag_ids: Optional[List[int]] = Field(
        default=None, description="Updated list of tag IDs"
    )
    short_description: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Updated brief description",
    )
    content: Optional[str] = Field(
        default=None, min_length=1, description="Updated guide content"
    )


class TagCreateSchema(BaseEmbedSchema):
    """Schema for creating new tags.

    Attributes:
        name (str): Tag name.
        description (str): Tag description.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    description: str = Field(
        ..., min_length=1, max_length=500, description="Tag description"
    )


class TagUpdateSchema(BaseEmbedSchema):
    """Schema for updating existing tags.

    Attributes:
        name (Optional[str]): Updated tag name.
        slug (Optional[str]): Updated URL-friendly slug.
        description (Optional[str]): Updated tag description.
    """

    name: Optional[str] = Field(
        default=None, min_length=1, max_length=100, description="Updated tag name"
    )
    slug: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated URL-friendly slug",
    )
    description: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Updated tag description",
    )


class GuideListSchema(BaseEmbedSchema):
    """Simplified guide schema for list views.

    Attributes:
        title (str): Guide title.
        slug (str): URL-friendly slug.
        short_description (str): Brief description.
        created_at (Optional[datetime]): When guide was created.
        updated_at (Optional[datetime]): When guide was last updated.
        game (Optional[GameSchema]): Associated game.
        tags (Optional[List[TagSchema]]): Associated tags.
    """

    title: str = Field(..., description="Guide title")
    slug: str = Field(..., description="URL-friendly slug")
    short_description: str = Field(..., description="Brief description")
    created_at: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    game: Optional[GameSchema] = Field(default=None, description="Associated game")
    tags: Optional[List[TagSchema]] = Field(default=None, description="Associated tags")


class TagListSchema(BaseEmbedSchema):
    """Simplified tag schema for list views.

    Attributes:
        name (str): Tag name.
        slug (str): URL-friendly slug.
        description (str): Tag description.
    """

    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="URL-friendly slug")
    description: str = Field(..., description="Tag description")
