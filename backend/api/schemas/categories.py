from typing import Any

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema, SlugMixin


class CategoryBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Category` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the category.
        name (str): Category name (e.g., "Any%", "100%").
        slug (str): URL-friendly version.
        type (str): Whether this is per-game or per-level category.
        url (str): Link to category on Speedrun.com.
        rules (str | None): Category-specific rules text.
        appear_on_main (bool): Whether to show on main page.
        archive (bool): Whether category is hidden from listings.
    """

    id: str = Field(..., description="Speedrun.com category ID")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL-friendly category slug")
    type: str = Field(
        ...,
        description="Category type",
        pattern="^(per-level|per-game)$",
    )
    url: str = Field(..., description="Speedrun.com URL for this category")
    rules: str | None = Field(
        default=None,
        max_length=1000,
        description="Category-specific rules and requirements",
    )
    appear_on_main: bool = Field(
        default=False, description="Whether this category appears on the main page"
    )
    archive: bool = Field(
        default=False, description="Whether this category is hidden from listings"
    )


class CategorySchema(CategoryBaseSchema):
    """Complete category schema with optional embedded data.

    Extends the base schema to include optional embedded game data when requested
    via ?embed=game parameter.

    Attributes:
        game (dict | None): Game this category belongs to - included with ?embed=game.
        variables (List[dict] | None): Category variables - included with ?embed=variables.
        values (List[dict] | None): Variables with values - included with ?embed=values.
    """

    game: dict | None = Field(
        None, description="Game this category belongs to - included with ?embed=game"
    )
    variables: list[dict] | None = Field(
        None,
        description="Category variables/subcategories - included with ?embed=variables",
    )
    # Note: This would include variables WITH their possible values
    # Takes precedence over 'variables' embed if both are requested
    values: list[dict] | None = Field(
        None, description="Variables with their values - included with ?embed=values"
    )

    @field_validator("game", mode="before")
    @classmethod
    def convert_model_to_none(cls, v: Any) -> dict | None:
        """Convert Django model instance to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        return None

    @field_validator("variables", "values", mode="before")
    @classmethod
    def convert_list_to_none(cls, v: Any) -> list[dict] | None:
        """Convert Django QuerySet or Manager to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if hasattr(v, "all"):
            return None
        return v


class CategoryCreateSchema(BaseEmbedSchema):
    """Schema for creating new categories.

    Used for POST /categories endpoints.
    Game ID is required to link the category to a game.

    Attributes:
        id (str | None): The category ID; if one is not given, it will auto-generate.
        game_id (str): ID of the game this category belongs to.
        name (str): The category name.
        slug (str): URL-friendly version.
        type (str): The category type (per-level or per-game).
        url (str): Speedrun.com URL.
        rules (str | None): Category-specific rules.
        appear_on_main (bool): Whether to show on main page.
        archive (bool): Whether category is hidden.
    """

    id: str | None = Field(
        default=None,
        max_length=12,
        description="The category ID; if one is not given, it will auto-generate.",
    )
    game_id: str = Field(..., description="ID of the game this category belongs to")
    name: str = Field(..., description="Category name")
    slug: str = Field(..., max_length=50, description="URL-friendly category slug")
    type: str = Field(
        ..., pattern="^(per-level|per-game)$", description="Category type"
    )
    url: str = Field(..., description="Speedrun.com URL")
    rules: str | None = Field(default=None, description="Category-specific rules")
    appear_on_main: bool = Field(default=False, description="Show on main page")
    archive: bool = Field(default=False, description="Hide category")


class CategoryUpdateSchema(BaseEmbedSchema):
    """Schema for updating categories.

    Used for PUT/PATCH /categories/{id} endpoints.
    All fields optional for partial updates.

    Attributes:
        game_id (str | None): Unique ID (usually based on SRC) of the category.
        name (str | None): Updated category name.
        type (str | None): Updated category type.
        url (str | None): Updated URL.
        rules (str | None): Updated rules.
        appear_on_main (bool | None): Updated main page visibility.
        hidden (bool | None): Updated hidden status.
    """

    game_id: str | None = Field(default=None, description="Updated game ID")
    name: str | None = Field(default=None, description="Updated category name")
    type: str | None = Field(
        None, pattern="^(per-level|per-game)$", description="Updated category type"
    )
    url: str | None = Field(default=None, description="Updated URL")
    rules: str | None = Field(default=None, description="Updated rules")
    appear_on_main: bool | None = Field(
        None, description="Updated main page visibility"
    )
    archive: bool | None = Field(default=None, description="Updated archive status")
