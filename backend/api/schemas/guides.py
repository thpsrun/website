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

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from api.schemas.base import BaseEmbedSchema, SlugMixin, TimestampMixin
from api.schemas.games import GameSchema


class TagSchema(SlugMixin, BaseEmbedSchema):
    """
    Schema for guide tags (e.g., 'Tricks', 'Glitches', 'Beginner').
    
    Used to categorize guides and help users find related content.
    
    Attributes:
        name: Tag name (e.g., 'Tricks', 'Glitches')
        slug: URL-friendly version of name
        description: Description of what this tag represents
    """
    
    description: str = Field(..., description="Description of the tag")

    class Config:
        from_attributes = True


class GuideSchema(SlugMixin, TimestampMixin, BaseEmbedSchema):
    """
    Schema for user-submitted guides.
    
    Provides information on tricks, glitches, speedrun categories, etc.
    Supports optional embeds for related data (game, tags).
    
    Attributes:
        title: Guide title
        slug: URL-friendly version of title
        short_description: Brief description of guide content
        content: Full guide content (Markdown supported)
        created_at: When guide was created
        updated_at: When guide was last updated
        
    Optional Embeds:
        game: Associated game information
        tags: List of tags associated with this guide
    """
    
    title: str = Field(..., description="Guide title")
    short_description: str = Field(..., description="Brief description of guide content")
    content: str = Field(..., description="Full guide content (supports Markdown)")
    
    # Optional embeds
    game: Optional[GameSchema] = Field(None, description="Associated game (embed=game)")
    tags: Optional[List[TagSchema]] = Field(None, description="Guide tags (embed=tags)")

    class Config:
        from_attributes = True


class GuideCreateSchema(BaseModel):
    """
    Schema for creating new guides.
    
    Input validation for guide creation.
    Slug is auto-generated from title.
    
    Attributes:
        title: Guide title
        game_id: ID of associated game
        tag_ids: List of tag IDs to associate with guide
        short_description: Brief description
        content: Full guide content
    """
    
    title: str = Field(..., min_length=1, max_length=200, description="Guide title")
    game_id: str = Field(..., description="Associated game ID")
    tag_ids: Optional[List[int]] = Field(
        default=[], description="List of tag IDs to associate with guide"
    )
    short_description: str = Field(
        ..., min_length=1, max_length=500, description="Brief description of guide content"
    )
    content: str = Field(..., min_length=1, description="Full guide content (Markdown supported)")


class GuideUpdateSchema(BaseModel):
    """
    Schema for updating existing guides.
    
    All fields are optional for partial updates.
    
    Attributes:
        title: Updated guide title
        game_id: Updated associated game ID
        tag_ids: Updated list of tag IDs
        short_description: Updated brief description
        content: Updated full content
    """
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated guide title")
    game_id: Optional[str] = Field(None, description="Updated associated game ID")
    tag_ids: Optional[List[int]] = Field(None, description="Updated list of tag IDs")
    short_description: Optional[str] = Field(
        None, min_length=1, max_length=500, description="Updated brief description"
    )
    content: Optional[str] = Field(None, min_length=1, description="Updated guide content")


class TagCreateSchema(BaseModel):
    """
    Schema for creating new tags.
    
    Input validation for tag creation.
    Slug is auto-generated from name.
    
    Attributes:
        name: Tag name
        description: Tag description
    """
    
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    description: str = Field(..., min_length=1, max_length=500, description="Tag description")


class TagUpdateSchema(BaseModel):
    """
    Schema for updating existing tags.
    
    All fields are optional for partial updates.
    
    Attributes:
        name: Updated tag name
        description: Updated tag description
    """
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated tag name")
    description: Optional[str] = Field(
        None, min_length=1, max_length=500, description="Updated tag description"
    )


# Guide list response schemas
class GuideListSchema(BaseModel):
    """
    Simplified guide schema for list views.
    
    Contains essential information without full content
    to improve performance for list endpoints.
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
    """
    
    name: str
    slug: str
    description: str

    class Config:
        from_attributes = True