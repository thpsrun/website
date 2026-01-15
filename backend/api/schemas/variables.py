from typing import List, Optional

from pydantic import Field

from api.schemas.base import BaseEmbedSchema, SlugMixin


class VariableValueSchema(BaseEmbedSchema):
    """Base schema for `Variables` data without embeds.

    Attributes:
        value (str): Unique ID (usually based on SRC) of the variable.
        name (str): Human-readable name (e.g., "Hard Mode").
        slug (str): URL-friendly version.
        archive (bool): Whether this value is archived/hidden.
        rules (Optional[str]): Specific rules for this value choice.
    """

    value: str = Field(..., max_length=10, description="Speedrun.com variable value ID")
    name: str = Field(..., max_length=50, description="Value name")
    slug: str = Field(..., max_length=50, description="URL-friendly value slug")
    archive: bool = Field(
        default=False, description="Whether this value is archived/hidden from listings"
    )
    rules: Optional[str] = Field(
        default=None, max_length=1000, description="Rules specific to this value choice"
    )


class VariableBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base variable schema without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the variable.
        name (str): Variable name (e.g., "Difficulty").
        slug (str): URL-friendly version.
        scope (str): Where this variable applies (global, full-game, etc.).
        all_cats (bool): Whether variable applies to all categories.
        archive (bool): Whether variable is archived/hidden.
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
        default=False,
        description="Whether variable applies to all categories in the game",
    )
    archive: bool = Field(
        default=False, description="Whether variable is archived/hidden from listings"
    )


class VariableSchema(VariableBaseSchema):
    """Variable schema without embedded values.

    Attributes:
        game (Optional[dict]): Game this variable belongs to - included with ?embed=game.
        category (Optional[dict]): Specific category (if not all_cats) - included with
            ?embed=category.
        level (Optional[dict]): Specific level (if scope=single-level) - included with
            ?embed=level.
    """

    game: Optional[dict] = Field(None, description="Game this variable belongs to")
    category: Optional[dict] = Field(
        None, description="Specific category (if not all_cats)"
    )
    level: Optional[dict] = Field(
        None, description="Specific level (if scope=single-level)"
    )


class VariableWithValuesSchema(VariableSchema):
    """Variable schema with embedded possible values.

    Attributes:
        values (List[VariableValueSchema]): Possible values/choices for this variable.
    """

    values: List[VariableValueSchema] = Field(
        ..., description="Possible values/choices for this variable"
    )


class VariableCreateSchema(BaseEmbedSchema):
    """Schema for creating variables.

    Attributes:
        game_id (str): Game ID this variable belongs to.
        name (str): Variable name.
        scope (str): Where this variable applies.
        archive (bool): Whether variable is archived/hidden.
        category_id (Optional[str]): Specific category ID (if not all_cats).
        level_id (Optional[str]): Specific level ID (if scope=single-level).
    """

    game_id: str = Field(..., description="Game ID this variable belongs to")
    name: str = Field(..., max_length=50)
    scope: str = Field(..., pattern="^(global|full-game|all-levels|single-level)$")
    archive: bool = Field(default=False)
    category_id: Optional[str] = Field(
        None, description="Specific category ID (if not all_cats)"
    )
    level_id: Optional[str] = Field(
        None, description="Specific level ID (if scope=single-level)"
    )


class VariableUpdateSchema(BaseEmbedSchema):
    """Schema for updating variables.

    Attributes:
        game_id (Optional[str]): Updated game ID.
        name (Optional[str]): Updated variable name.
        scope (Optional[str]): Updated scope.
        all_cats (Optional[bool]): Updated all_cats flag.
        archive (Optional[bool]): Updated archive status.
        category_id (Optional[str]): Updated category ID.
        level_id (Optional[str]): Updated level ID.
    """

    game_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None, max_length=50)
    scope: Optional[str] = Field(
        None, pattern="^(global|full-game|all-levels|single-level)$"
    )
    all_cats: Optional[bool] = Field(default=None)
    archive: Optional[bool] = Field(default=None)
    category_id: Optional[str] = Field(default=None)
    level_id: Optional[str] = Field(default=None)
