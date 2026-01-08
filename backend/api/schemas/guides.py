"""
Guides API Schemas for Django Ninja

This module contains Pydantic schemas for the guides and tags models.
These schemas handle:
- User-submitted guides with tricks, glitches, and category information
- Tag system for categorizing guides
- Associated game information
- Markdown content support

Schema Types:
- TagSchema: Tag information (name, slug, description)
- GuideSchema: Complete guide information with optional embeds
- GuideCreateSchema: Input schema for creating guides
- GuideUpdateSchema: Input schema for updating guides
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from api.schemas.base import BaseEmbedSchema, SlugMixin, TimestampMixin
from api.schemas.games import GameSchema


class TagSchema(SlugMixin, BaseEmbedSchema):
    """
    Schema for guide tags (e.g., 'Tricks', 'Glitches', 'Beginner').

    Used to categorize guides and help users find related content.

    Attributes:
        name (str): Tag name (e.g., 'Tricks', 'Glitches')
        slug (str): URL-friendly version of name
        description (str): Description of what this tag represents
    """

    description: str = Field(..., description="Description of the tag")

    class Config:  # type: ignore
        from_attributes = True


class GuideSchema(SlugMixin, TimestampMixin, BaseEmbedSchema):
    """
    Schema for user-submitted guides.

    Provides information on tricks, glitches, speedrun categories, etc.
    Supports optional embeds for related data (game, tags).

    Attributes:
        title (str): Guide title
        slug (str): URL-friendly version of title
        short_description (str): Brief description of guide content
        content (str): Full guide content (Markdown supported)
        created_at (datetime): When guide was created
        updated_at (datetime): When guide was last updated
        game (Optional[GameSchema]): Associated game information - included with ?embed=game
        tags (Optional[List[TagSchema]]): List of tags associated with this guide.
    """

    title: str = Field(..., description="Guide title")
    short_description: str = Field(
        ..., description="Brief description of guide content"
    )
    content: str = Field(..., description="Full guide content (supports Markdown)")

    game: Optional[GameSchema] = Field(
        None, description="Associated game - included with ?embed=game"
    )
    tags: Optional[List[TagSchema]] = Field(
        None, description="Guide tags - included with ?embed=tags"
    )

    class Config:  # type: ignore
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class GuideCreateSchema(BaseModel):
    """
    Schema for creating new guides.

    Input validation for guide creation.
    Slug is auto-generated from title.

    Attributes:
        title (str): Guide title
        game_id (str): ID of associated game
        tag_ids (Optional[List[int]]): List of tag IDs to associate with guide
        short_description (str): Brief description
        content (str): Full guide content
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


class GuideUpdateSchema(BaseModel):
    """
    Schema for updating existing guides.

    All fields are optional for partial updates.

    Attributes:
        title (Optional[str]): Updated guide title
        game_id (Optional[str]): Updated associated game ID
        tag_ids (Optional[List[int]]): Updated list of tag IDs
        short_description (Optional[str]): Updated brief description
        content (Optional[str]): Updated full content
    """

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Updated guide title"
    )
    game_id: Optional[str] = Field(
        default=None, description="Updated associated game ID"
    )
    tag_ids: Optional[List[int]] = Field(
        default=None, description="Updated list of tag IDs"
    )
    short_description: Optional[str] = Field(
        None, min_length=1, max_length=500, description="Updated brief description"
    )
    content: Optional[str] = Field(
        None, min_length=1, description="Updated guide content"
    )


class TagCreateSchema(BaseModel):
    """
    Schema for creating new tags.

    Input validation for tag creation.
    Slug is auto-generated from name.

    Attributes:
        name (str): Tag name
        description (str): Tag description
    """

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    description: str = Field(
        ..., min_length=1, max_length=500, description="Tag description"
    )


class TagUpdateSchema(BaseModel):
    """
    Schema for updating existing tags.

    All fields are optional for partial updates.

    Attributes:
        name (Optional[str]): Updated tag name
        description (Optional[str]): Updated tag description
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Updated tag name"
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=500, description="Updated tag description"
    )


# Guide list response schemas
class GuideListSchema(BaseModel):
    """
    Simplified guide schema for list views.

    Contains essential information without full content
    to improve performance for list endpoints.

    Attributes:
        title (str): Guide title
        slug (str): URL-friendly slug
        short_description (str): Brief description
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
        game (Optional[GameSchema]): Associated game
        tags (Optional[List[TagSchema]]): Associated tags
    """

    title: str
    slug: str
    short_description: str
    created_at: datetime
    updated_at: datetime
    game: Optional[GameSchema] = None
    tags: Optional[List[TagSchema]] = None

    class Config:
        from_attributes = True


class TagListSchema(BaseModel):
    """
    Simplified tag schema for list views.

    Attributes:
        name (str): Tag name
        slug (str): URL-friendly slug
        description (str): Tag description
    """

    name: str
    slug: str
    description: str

    class Config:
        from_attributes = True
