from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class VariableValueSchema(BaseEmbedSchema):
    """
    Schema for VariableValues (individual choices within a variable).

    For example, if a variable is "Difficulty", the values might be
    "Easy", "Normal", "Hard" - each with their own ID and slug.

    Attributes:
        value (str): The unique ID for this value
        name (str): Human-readable name (e.g., "Hard Mode")
        slug (str): URL-friendly version
        hidden (bool): Whether this value is hidden
        rules (Optional[str]): Specific rules for this value choice
    """

    value: str = Field(
        ..., max_length=10, description="Speedrun.com variable value ID"
    )
    name: str = Field(..., max_length=50, description="Value name")
    slug: str = Field(..., max_length=50, description="URL-friendly value slug")
    hidden: bool = Field(
        default=False, description="Whether this value is hidden from listings"
    )
    rules: Optional[str] = Field(
        default=None, max_length=1000, description="Rules specific to this value choice"
    )


class VariableBaseSchema(SlugMixin, BaseEmbedSchema):
    """
    Base variable schema without embeds.

    Variables are subcategories/filters within speedrun categories.
    For example: difficulty settings, character choices, etc.

    Attributes:
        id (str): Speedrun.com variable ID
        name (str): Variable name (e.g., "Difficulty")
        slug (str): URL-friendly version
        scope (str): Where this variable applies (global, full-game, etc.)
        all_cats (bool): Whether variable applies to all categories
        hidden (bool): Whether variable is hidden
    """

    id: str = Field(..., max_length=10, description="Speedrun.com variable ID")
    name: str = Field(..., max_length=50, description="Variable name")
    slug: str = Field(..., max_length=50, description="URL-friendly variable slug")
    scope: str = Field(
        ...,
        description="Where this variable applies",
        pattern="^(global|full-game|all-levels|single-level)$",
    )
    all_cats: bool = Field(
        default=False, description="Whether variable applies to all categories in the game"
    )
    hidden: bool = Field(
        default=False, description="Whether variable is hidden from listings"
    )


class VariableSchema(VariableBaseSchema):
    """
    Variable schema without embedded values.

    Used when we want variable info but don't need the full
    list of possible values for each variable.

    Attributes:
        game (Optional[dict]): Game this variable belongs to - included with ?embed=game
        category (Optional[dict]): Specific category (if not all_cats) - included with ?embed=category
        level (Optional[dict]): Specific level (if scope=single-level) - included with ?embed=level
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

    Attributes:
        values (List[VariableValueSchema]): Possible values/choices for this variable
    """

    values: List[VariableValueSchema] = Field(
        ..., description="Possible values/choices for this variable"
    )


# Simplified create/update schemas
class VariableCreateSchema(BaseEmbedSchema):
    """
    Schema for creating variables.

    Attributes:
        game_id (str): Game ID this variable belongs to
        name (str): Variable name
        scope (str): Where this variable applies
        hidden (bool): Whether variable is hidden
        category_id (Optional[str]): Specific category ID (if not all_cats)
        level_id (Optional[str]): Specific level ID (if scope=single-level)
    """

    game_id: str = Field(..., description="Game ID this variable belongs to")
    name: str = Field(..., max_length=50)
    scope: str = Field(..., pattern="^(global|full-game|all-levels|single-level)$")
    hidden: bool = Field(default=False)
    category_id: Optional[str] = Field(
        None, description="Specific category ID (if not all_cats)"
    )
    level_id: Optional[str] = Field(
        None, description="Specific level ID (if scope=single-level)"
    )


class VariableUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating variables.

    Attributes:
        game_id (Optional[str]): Updated game ID
        name (Optional[str]): Updated variable name
        scope (Optional[str]): Updated scope
        all_cats (Optional[bool]): Updated all_cats flag
        hidden (Optional[bool]): Updated hidden status
        category_id (Optional[str]): Updated category ID
        level_id (Optional[str]): Updated level ID
    """

    game_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None, max_length=50)
    scope: Optional[str] = Field(
        None, pattern="^(global|full-game|all-levels|single-level)$"
    )
    all_cats: Optional[bool] = Field(default=None)
    hidden: Optional[bool] = Field(default=None)
    category_id: Optional[str] = Field(default=None)
    level_id: Optional[str] = Field(default=None)
