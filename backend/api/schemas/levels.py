"""
Levels Schemas for Django Ninja API

Schemas for the Levels model. Levels represent individual stages/maps
within games that can be speedrun separately (Individual Level runs).

Key Features:
- Game relationship (which game this level belongs to)
- Auto-generated slugs from level names
- Optional rules specific to the level
- Used for Individual Level (IL) speedrun categories
"""

from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class LevelBaseSchema(SlugMixin, BaseEmbedSchema):
    """
    Base level schema without embeds.

    Contains core level data without any embedded relationships.

    Attributes:
        id: Speedrun.com level ID
        name: Level name (e.g., "Warehouse", "School")
        slug: URL-friendly version
        url: Link to level on Speedrun.com
        rules: Level-specific rules text
    """

    id: str = Field(
        ..., max_length=10, description="Speedrun.com level ID", example="592pxj8d"
    )
    name: str = Field(..., max_length=75, description="Level name", example="Warehouse")
    slug: str = Field(
        ..., max_length=75, description="URL-friendly level slug", example="warehouse"
    )
    url: str = Field(
        ...,
        description="Speedrun.com URL for this level",
        example="https://www.speedrun.com/thps1/level/Warehouse",
    )
    rules: Optional[str] = Field(
        None, max_length=1000, description="Level-specific rules and requirements"
    )


class LevelSchema(LevelBaseSchema):
    """
    Complete level schema with optional embedded data.

    Extends the base schema to include optional embedded game data
    and variables when requested via embed parameters.

    Supported Embeds:
        - game: Include the game this level belongs to
        - variables: Include level-specific variables/subcategories
        - values: Include variables and their possible values

    Example Usage:
        GET /levels/592pxj8d -> Basic level data
        GET /levels/592pxj8d?embed=game -> Level with game data
        GET /levels/592pxj8d?embed=variables -> Level with subcategories
    """


    game: Optional[dict] = Field(
        None, description="Game this level belongs to - included with ?embed=game"
    )
    variables: Optional[List[dict]] = Field(
        None,
        description="Level-specific variables/subcategories - included with ?embed=variables",
    )
    # Note: This includes variables WITH their possible values
    # Takes precedence over 'variables' embed if both are requested
    values: Optional[List[dict]] = Field(
        None, description="Variables with their values - included with ?embed=values"
    )


class LevelCreateSchema(BaseEmbedSchema):
    """
    Schema for creating new levels.

    Used for POST /levels endpoints.
    Game ID is required to link the level to a game.
    """

    game_id: str = Field(..., description="ID of the game this level belongs to")
    name: str = Field(..., max_length=75)
    url: str = Field(...)
    rules: Optional[str] = Field(None, max_length=1000)
    # Note: slug auto-generated from name


class LevelUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating levels.

    Used for PUT/PATCH /levels/{id} endpoints.
    All fields optional for partial updates.
    """

    game_id: Optional[str] = Field(None)
    name: Optional[str] = Field(None, max_length=75)
    url: Optional[str] = Field(None)
    rules: Optional[str] = Field(None, max_length=1000)
