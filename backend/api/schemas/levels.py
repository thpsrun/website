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
        id (str): Speedrun.com level ID
        name (str): Level name (e.g., "Warehouse", "School")
        slug (str): URL-friendly version
        url (str): Link to level on Speedrun.com
        rules (Optional[str]): Level-specific rules text
    """

    id: str = Field(..., max_length=10, description="Speedrun.com level ID")
    name: str = Field(..., max_length=75, description="Level name")
    slug: str = Field(..., max_length=75, description="URL-friendly level slug")
    url: str = Field(..., description="Speedrun.com URL for this level")
    rules: Optional[str] = Field(
        default=None, max_length=1000, description="Level-specific rules and requirements"
    )


class LevelSchema(LevelBaseSchema):
    """
    Complete level schema with optional embedded data.

    Extends the base schema to include optional embedded game data
    and variables when requested via embed parameters.

    Attributes:
        game (Optional[dict]): Game this level belongs to - included with ?embed=game
        variables (Optional[List[dict]]): Level-specific variables - included with ?embed=variables
        values (Optional[List[dict]]): Variables with values - included with ?embed=values

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

    Attributes:
        game_id (str): ID of the game this level belongs to
        name (str): Level name
        url (str): Speedrun.com URL
        rules (Optional[str]): Level-specific rules
    """

    game_id: str = Field(..., description="ID of the game this level belongs to")
    name: str = Field(..., description="Level name")
    url: str = Field(..., description="Speedrun.com URL")
    rules: Optional[str] = Field(default=None, description="Level-specific rules")
    # Note: slug auto-generated from name


class LevelUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating levels.

    Used for PUT/PATCH /levels/{id} endpoints.
    All fields optional for partial updates.

    Attributes:
        game_id (Optional[str]): Updated game ID
        name (Optional[str]): Updated level name
        url (Optional[str]): Updated URL
        rules (Optional[str]): Updated rules
    """

    game_id: Optional[str] = Field(default=None, description="Updated game ID")
    name: Optional[str] = Field(default=None, description="Updated level name")
    url: Optional[str] = Field(default=None, description="Updated URL")
    rules: Optional[str] = Field(default=None, description="Updated rules")
