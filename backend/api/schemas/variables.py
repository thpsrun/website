"""
Variables Schemas for Django Ninja API

Schemas for Variables and VariableValues models. Variables represent
subcategories or filters within speedrun categories (like difficulty
settings, character choices, etc.).

This is one of the more complex schemas due to the relationships:
- Variables belong to games and/or specific categories
- Variables can apply to all categories or just specific ones
- Variables have multiple possible values (VariableValues)
- Variables have different scopes (global, full-game, IL-specific)

Key Features:
- Complex validation logic (replicated from model.clean())
- Nested VariableValues for the full subcategory system
- Flexible scope system for different run types
"""

from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class VariableValueSchema(BaseEmbedSchema):
    """
    Schema for VariableValues (individual choices within a variable).

    For example, if a variable is "Difficulty", the values might be
    "Easy", "Normal", "Hard" - each with their own ID and slug.

    Attributes:
        value: The unique ID for this value
        name: Human-readable name (e.g., "Hard Mode")
        slug: URL-friendly version
        hidden: Whether this value is hidden
        rules: Specific rules for this value choice
    """

    value: str = Field(
        ...,
        max_length=10,
        description="Speedrun.com variable value ID",
        example="zqoee4k1",
    )
    name: str = Field(..., max_length=50, description="Value name", example="Hard Mode")
    slug: str = Field(
        ..., max_length=50, description="URL-friendly value slug", example="hard-mode"
    )
    hidden: bool = Field(
        False, description="Whether this value is hidden from listings"
    )
    rules: Optional[str] = Field(
        None, max_length=1000, description="Rules specific to this value choice"
    )


class VariableBaseSchema(SlugMixin, BaseEmbedSchema):
    """
    Base variable schema without embeds.

    Variables are subcategories/filters within speedrun categories.
    For example: difficulty settings, character choices, etc.

    Attributes:
        id: Speedrun.com variable ID
        name: Variable name (e.g., "Difficulty")
        slug: URL-friendly version
        scope: Where this variable applies (global, full-game, etc.)
        all_cats: Whether variable applies to all categories
        hidden: Whether variable is hidden
    """

    id: str = Field(
        ..., max_length=10, description="Speedrun.com variable ID", example="5lygdn8q"
    )
    name: str = Field(
        ..., max_length=50, description="Variable name", example="Difficulty"
    )
    slug: str = Field(
        ...,
        max_length=50,
        description="URL-friendly variable slug",
        example="difficulty",
    )
    scope: str = Field(
        ...,
        description="Where this variable applies",
        example="full-game",
        pattern="^(global|full-game|all-levels|single-level)$",
    )
    all_cats: bool = Field(
        False, description="Whether variable applies to all categories in the game"
    )
    hidden: bool = Field(False, description="Whether variable is hidden from listings")


class VariableSchema(VariableBaseSchema):
    """
    Variable schema without embedded values.

    Used when we want variable info but don't need the full
    list of possible values for each variable.
    """


    game: Optional[dict] = Field(
        None, description="Game this variable belongs to - included with ?embed=game"
    )
    category: Optional[dict] = Field(
        None,
        description="Specific category (if not all_cats) - included with ?embed=category",
    )
    level: Optional[dict] = Field(
        None,
        description="Specific level (if scope=single-level) - included with ?embed=level",
    )


class VariableWithValuesSchema(VariableSchema):
    """
    Variable schema with embedded possible values.

    This is used when we want the full subcategory system
    including all the possible choices for each variable.

    Takes precedence over VariableSchema when both are requested.
    """

    values: List[VariableValueSchema] = Field(
        ..., description="Possible values/choices for this variable"
    )


# Simplified create/update schemas
class VariableCreateSchema(BaseEmbedSchema):
    """Schema for creating variables."""

    game_id: str = Field(..., description="Game ID this variable belongs to")
    name: str = Field(..., max_length=50)
    scope: str = Field(..., pattern="^(global|full-game|all-levels|single-level)$")
    all_cats: bool = Field(False)
    hidden: bool = Field(False)
    category_id: Optional[str] = Field(
        None, description="Specific category ID (if not all_cats)"
    )
    level_id: Optional[str] = Field(
        None, description="Specific level ID (if scope=single-level)"
    )


class VariableUpdateSchema(BaseEmbedSchema):
    """Schema for updating variables."""

    game_id: Optional[str] = Field(None)
    name: Optional[str] = Field(None, max_length=50)
    scope: Optional[str] = Field(
        None, pattern="^(global|full-game|all-levels|single-level)$"
    )
    all_cats: Optional[bool] = Field(None)
    hidden: Optional[bool] = Field(None)
    category_id: Optional[str] = Field(None)
    level_id: Optional[str] = Field(None)
