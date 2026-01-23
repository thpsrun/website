from typing import Any

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema, SlugMixin


class VariableValueSchema(BaseEmbedSchema):
    """Schema for `VariableValues` data with optional embeds.

    Attributes:
        value (str): Unique ID (usually based on SRC) of the variable value.
        name (str): Human-readable name (e.g., "Hard Mode").
        slug (str): URL-friendly version.
        archive (bool): Whether this value is archived/hidden.
        rules (str | None): Specific rules for this value choice.
        variable (dict | None): Variable this value belongs to - included with ?embed=variable.
    """

    value: str = Field(..., max_length=10, description="Speedrun.com variable value ID")
    name: str = Field(..., max_length=50, description="Value name")
    slug: str = Field(..., max_length=50, description="URL-friendly value slug")
    archive: bool = Field(
        default=False, description="Whether this value is archived/hidden from listings"
    )
    rules: str | None = Field(
        default=None, max_length=1000, description="Rules specific to this value choice"
    )
    variable: dict | None = Field(None, description="Variable this value belongs to")

    @field_validator("variable", mode="before")
    @classmethod
    def convert_model_to_none(cls, v: Any) -> dict | None:
        """Convert Django model instance to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        return None


class VariableBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base variable schema without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the variable.
        name (str): Variable name (e.g., "Difficulty").
        slug (str): URL-friendly version.
        scope (str): Where this variable applies (global, full-game, etc.).
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
    archive: bool = Field(
        default=False, description="Whether variable is archived/hidden from listings"
    )


class VariableSchema(VariableBaseSchema):
    """Variable schema without embedded values.

    Attributes:
        game (dict | None): Game this variable belongs to - included with ?embed=game.
        category (dict | None): Specific category - included with ?embed=category.
        level (dict | None): Specific level (if scope=single-level) - included with
            ?embed=level.
    """

    game: dict | None = Field(None, description="Game this variable belongs to")
    category: dict | None = Field(None, description="Specific category")
    level: dict | None = Field(
        None, description="Specific level (if scope=single-level)"
    )

    @field_validator("game", "category", "level", mode="before")
    @classmethod
    def convert_model_to_none(cls, v: Any) -> dict | None:
        """Convert Django model instance to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # If it's a Django model, return None (embeds will be applied separately)
        return None


class VariableWithValuesSchema(VariableSchema):
    """Variable schema with embedded possible values.

    Attributes:
        values (List[VariableValueSchema]): Possible values/choices for this variable.
    """

    values: list[VariableValueSchema] = Field(
        ..., description="Possible values/choices for this variable"
    )


class VariableCreateSchema(BaseEmbedSchema):
    """Schema for creating variables.

    Attributes:
        id (str | None): The variable ID; if one is not given, it will auto-generate.
        game_id (str): Game ID this variable belongs to.
        name (str): Variable name.
        slug (str): URL-friendly version.
        scope (str): Where this variable applies.
        archive (bool): Whether variable is archived/hidden.
        category_id (str | None): Specific category ID (if not all_cats).
        level_id (str | None): Specific level ID (if scope=single-level).
    """

    id: str | None = Field(
        default=None,
        max_length=12,
        description="The variable ID; if one is not given, it will auto-generate.",
    )
    game_id: str = Field(..., description="Game ID this variable belongs to")
    name: str = Field(..., max_length=50)
    slug: str = Field(..., max_length=50, description="URL-friendly variable slug")
    scope: str = Field(..., pattern="^(global|full-game|all-levels|single-level)$")
    archive: bool = Field(default=False)
    category_id: str | None = Field(
        None, description="Specific category ID (if not all_cats)"
    )
    level_id: str | None = Field(
        None, description="Specific level ID (if scope=single-level)"
    )


class VariableUpdateSchema(BaseEmbedSchema):
    """Schema for updating variables.

    Attributes:
        game_id (str | None): Updated game ID.
        name (str | None): Updated variable name.
        scope (str | None): Updated scope.
        archive (bool | None): Updated archive status.
        category_id (str | None): Updated category ID.
        level_id (str | None): Updated level ID.
    """

    game_id: str | None = Field(default=None)
    name: str | None = Field(default=None, max_length=50)
    scope: str | None = Field(
        None, pattern="^(global|full-game|all-levels|single-level)$"
    )
    archive: bool | None = Field(default=None)
    category_id: str | None = Field(default=None)
    level_id: str | None = Field(default=None)


class VariableValueCreateSchema(BaseEmbedSchema):
    """Schema for creating variable values.

    Attributes:
        value (str | None): The value ID; if one is not given, it will auto-generate.
        variable_id (str): Variable ID this value belongs to.
        name (str): Value name.
        slug (str | None): URL-friendly version; auto-generated from name if not provided.
        archive (bool): Whether value is archived/hidden.
        rules (str | None): Rules specific to this value choice.
    """

    value: str | None = Field(
        default=None,
        max_length=10,
        description="The value ID; if one is not given, it will auto-generate.",
    )
    variable_id: str = Field(..., description="Variable ID this value belongs to")
    name: str = Field(..., max_length=50)
    slug: str | None = Field(
        default=None,
        max_length=50,
        description="URL-friendly slug; auto-generated from name if not provided",
    )
    archive: bool = Field(default=False)
    rules: str | None = Field(default=None, max_length=1000)


class VariableValueUpdateSchema(BaseEmbedSchema):
    """Schema for updating variable values.

    Attributes:
        variable_id (str | None): Updated variable ID.
        name (str | None): Updated value name.
        slug (str | None): Updated URL-friendly slug.
        archive (bool | None): Updated archive status.
        rules (str | None): Updated rules.
    """

    variable_id: str | None = Field(default=None)
    name: str | None = Field(default=None, max_length=50)
    slug: str | None = Field(default=None, max_length=50)
    archive: bool | None = Field(default=None)
    rules: str | None = Field(default=None, max_length=1000)
