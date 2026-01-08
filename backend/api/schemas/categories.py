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
        id (str): Speedrun.com category ID
        name (str): Category name (e.g., "Any%", "100%")
        slug (str): URL-friendly version
        type (str): Whether this is per-game or per-level category
        url (str): Link to category on Speedrun.com
        rules (Optional[str]): Category-specific rules text
        appear_on_main (bool): Whether to show on main page
        hidden (bool): Whether category is hidden from listings
    """

    id: str = Field(..., description="Speedrun.com category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly category slug")
    type: str = Field(
        ...,
        description="Category type",
        pattern="^(per-level|per-game)$",  # Only these values allowed
    )
    url: str = Field(..., description="Speedrun.com URL for this category")
    rules: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Category-specific rules and requirements",
    )
    appear_on_main: bool = Field(
        default=False, description="Whether this category appears on the main page"
    )
    hidden: bool = Field(
        default=False, description="Whether this category is hidden from listings"
    )


class CategorySchema(CategoryBaseSchema):
    """
    Complete category schema with optional embedded data.

    Extends the base schema to include optional embedded game data
    when requested via ?embed=game parameter.

    Attributes:
        game (Optional[dict]): Game this category belongs to - included with ?embed=game
        variables (Optional[List[dict]]): Category variables - included with ?embed=variables
        values (Optional[List[dict]]): Variables with values - included with ?embed=values

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

    Attributes:
        game_id (str): ID of the game this category belongs to
        name (str): Category name
        type (str): Category type (per-level or per-game)
        url (str): Speedrun.com URL
        rules (Optional[str]): Category-specific rules
        appear_on_main (bool): Whether to show on main page
        hidden (bool): Whether category is hidden
    """

    game_id: str = Field(..., description="ID of the game this category belongs to")
    name: str = Field(..., description="Category name")
    type: str = Field(
        ..., pattern="^(per-level|per-game)$", description="Category type"
    )
    url: str = Field(..., description="Speedrun.com URL")
    rules: Optional[str] = Field(default=None, description="Category-specific rules")
    appear_on_main: bool = Field(default=False, description="Show on main page")
    hidden: bool = Field(default=False, description="Hide category")
    # Note: slug auto-generated from name


class CategoryUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating categories.

    Used for PUT/PATCH /categories/{id} endpoints.
    All fields optional for partial updates.

    Attributes:
        game_id (Optional[str]): Updated game ID
        name (Optional[str]): Updated category name
        type (Optional[str]): Updated category type
        url (Optional[str]): Updated URL
        rules (Optional[str]): Updated rules
        appear_on_main (Optional[bool]): Updated main page visibility
        hidden (Optional[bool]): Updated hidden status
    """

    game_id: Optional[str] = Field(default=None, description="Updated game ID")
    name: Optional[str] = Field(default=None, description="Updated category name")
    type: Optional[str] = Field(
        None, pattern="^(per-level|per-game)$", description="Updated category type"
    )
    url: Optional[str] = Field(default=None, description="Updated URL")
    rules: Optional[str] = Field(default=None, description="Updated rules")
    appear_on_main: Optional[bool] = Field(
        None, description="Updated main page visibility"
    )
    hidden: Optional[bool] = Field(default=None, description="Updated hidden status")
