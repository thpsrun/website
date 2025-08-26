"""
Categories Schemas for Django Ninja API

Schemas for the Categories model. Categories represent different types
of speedrun categories like Any%, 100%, Low%, etc.

Categories can be:
- per-game: Full game speedruns (Any%, 100%)
- per-level: Individual level runs

Key Features:
- Game relationship (which game this category belongs to)
- Type validation (per-game vs per-level)
- Optional embedded game data
- Rules text for category-specific rules
"""

from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class CategoryBaseSchema(SlugMixin, BaseEmbedSchema):
    """
    Base category schema without embeds.

    Contains core category data without any embedded relationships.

    Attributes:
        id: Speedrun.com category ID
        name: Category name (e.g., "Any%", "100%")
        slug: URL-friendly version
        type: Whether this is per-game or per-level category
        url: Link to category on Speedrun.com
        rules: Category-specific rules text
        appear_on_main: Whether to show on main page
        hidden: Whether category is hidden from listings
    """

    id: str = Field(
        ..., max_length=10, description="Speedrun.com category ID", example="rklge08d"
    )
    name: str = Field(..., max_length=50, description="Category name", example="Any%")
    slug: str = Field(
        ...,
        max_length=50,
        description="URL-friendly category slug",
        example="any-percent",
    )
    type: str = Field(
        ...,
        description="Category type",
        example="per-game",
        pattern="^(per-level|per-game)$",  # Only these values allowed
    )
    url: str = Field(
        ...,
        description="Speedrun.com URL for this category",
        example="https://www.speedrun.com/thps4#Any",
    )
    rules: Optional[str] = Field(
        None, max_length=1000, description="Category-specific rules and requirements"
    )
    appear_on_main: bool = Field(
        False, description="Whether this category appears on the main page"
    )
    hidden: bool = Field(
        False, description="Whether this category is hidden from listings"
    )


class CategorySchema(CategoryBaseSchema):
    """
    Complete category schema with optional embedded data.

    Extends the base schema to include optional embedded game data
    when requested via ?embed=game parameter.

    Supported Embeds:
        - game: Include the game this category belongs to
        - variables: Include category variables/subcategories
        - values: Include variables and their possible values

    Note: The 'values' embed takes precedence over 'variables' embed
    as it includes the same data plus the variable values.
    """


    game: Optional[dict] = Field(
        None, description="Game this category belongs to - included with ?embed=game"
    )
    variables: Optional[List[dict]] = Field(
        None,
        description="Category variables/subcategories - included with ?embed=variables",
    )
    # Note: This would include variables WITH their possible values
    # Takes precedence over 'variables' embed if both are requested
    values: Optional[List[dict]] = Field(
        None, description="Variables with their values - included with ?embed=values"
    )


class CategoryCreateSchema(BaseEmbedSchema):
    """
    Schema for creating new categories.

    Used for POST /categories endpoints.
    Game ID is required to link the category to a game.
    """

    game_id: str = Field(..., description="ID of the game this category belongs to")
    name: str = Field(..., max_length=50)
    type: str = Field(..., pattern="^(per-level|per-game)$")
    url: str = Field(...)
    rules: Optional[str] = Field(None, max_length=1000)
    appear_on_main: bool = Field(False)
    hidden: bool = Field(False)
    # Note: slug auto-generated from name


class CategoryUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating categories.

    Used for PUT/PATCH /categories/{id} endpoints.
    All fields optional for partial updates.
    """

    game_id: Optional[str] = Field(None)
    name: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, pattern="^(per-level|per-game)$")
    url: Optional[str] = Field(None)
    rules: Optional[str] = Field(None, max_length=1000)
    appear_on_main: Optional[bool] = Field(None)
    hidden: Optional[bool] = Field(None)
