from datetime import datetime

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
        created_at (datetime | None): When guide was created.
        updated_at (datetime | None): When guide was last updated.
        game (GameSchema | None): Associated game - included with ?embed=game.
        tags (list[TagSchema] | None): Associated tags - included with ?embed=tags.
    """

    title: str = Field(..., description="Guide title")
    short_description: str = Field(
        ..., description="Brief description of guide content"
    )
    content: str = Field(..., description="Full guide content (supports Markdown)")

    game: GameSchema | None = Field(default=None, description="Associated game")
    tags: list[TagSchema] | None = Field(default=None, description="Guide tags")


class GuideCreateSchema(BaseEmbedSchema):
    """Schema for creating new guides.

    Attributes:
        title (str): Guide title.
        game_id (str): Associated game ID.
        tag_ids (list[TagSchema] | None): List of tag IDs to associate with guide.
        short_description (str): Brief description.
        content (str): Full guide content.
    """

    title: str = Field(..., min_length=1, max_length=200, description="Guide title")
    game_id: str = Field(..., description="Associated game ID")
    tag_ids: list[int] | None = Field(
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
        title (str | None): Updated guide title.
        slug (str | None): Updated URL-friendly slug.
        game_id (str | None): Updated associated game ID.
        tag_ids (list[str] | None): Updated list of tag IDs.
        short_description (str | None): Updated brief description.
        content (str | None): Updated full content.
    """

    title: str | None = Field(
        default=None, min_length=1, max_length=200, description="Updated guide title"
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated URL-friendly slug",
    )
    game_id: str | None = Field(default=None, description="Updated associated game ID")
    tag_ids: list[str] | None = Field(
        default=None, description="Updated list of tag IDs"
    )
    short_description: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Updated brief description",
    )
    content: str | None = Field(
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
        name (str | None): Updated tag name.
        slug (str | None): Updated URL-friendly slug.
        description (str | None): Updated tag description.
    """

    name: str | None = Field(
        default=None, min_length=1, max_length=100, description="Updated tag name"
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated URL-friendly slug",
    )
    description: str | None = Field(
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
        created_at (datetime | None): When guide was created.
        updated_at (datetime | None): When guide was last updated.
        game (GameSchema | None): Associated game.
        tags (list[TagSchema] | None): Associated tags.
    """

    title: str = Field(..., description="Guide title")
    slug: str = Field(..., description="URL-friendly slug")
    short_description: str = Field(..., description="Brief description")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )
    game: GameSchema | None = Field(default=None, description="Associated game")
    tags: list[TagSchema] | None = Field(default=None, description="Associated tags")


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
