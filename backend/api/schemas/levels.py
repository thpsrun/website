from typing import Any

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema, SlugMixin


class LevelBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Levels` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the level.
        name (str): Level name (e.g., "Warehouse", "School").
        slug (str): URL-friendly version.
        url (str): Link to level on Speedrun.com.
        rules (str | None): Level-specific rules text.
    """

    id: str = Field(..., max_length=10, description="Speedrun.com level ID")
    name: str = Field(..., max_length=75, description="Level name")
    slug: str = Field(..., max_length=75, description="URL-friendly level slug")
    url: str = Field(..., description="Speedrun.com URL for this level")
    rules: str | None = Field(
        default=None,
        max_length=1000,
        description="Level-specific rules and requirements",
    )


class LevelSchema(LevelBaseSchema):
    """Complete level schema with optional embedded data.

    Attributes:
        game (dict | None): Game this level belongs to - included with ?embed=game.
        variables (List[dict] | None): Level-specific variables - included with ?embed=variables.
        values (List[dict] | None): Variables with values - included with ?embed=values.
    """

    game: dict | None = Field(None, description="Game this level belongs to")
    variables: list[dict] | None = Field(
        None,
        description="Level-specific variables/subcategories",
    )
    values: list[dict] | None = Field(None, description="Variables with their values")

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


class LevelCreateSchema(BaseEmbedSchema):
    """Schema for creating new levels.

    Attributes:
        id (str | None): The level ID; if one is not given, it will auto-generate.
        game_id (str): Game ID this level belongs to.
        name (str): Level name.
        slug (str): URL-friendly version.
        url (str): Speedrun.com URL.
        rules (str | None): Level-specific rules.
    """

    id: str | None = Field(
        default=None,
        max_length=12,
        description="The level ID; if one is not given, it will auto-generate.",
    )
    game_id: str = Field(..., description="ID of the game this level belongs to")
    name: str = Field(..., max_length=75, description="Level name")
    slug: str = Field(..., max_length=75, description="URL-friendly level slug")
    url: str = Field(..., description="Speedrun.com URL")
    rules: str | None = Field(default=None, description="Level-specific rules")


class LevelUpdateSchema(BaseEmbedSchema):
    """Schema for updating levels.

    Attributes:
        game_id (str | None): Updated game ID.
        name (str | None): Updated level name.
        url (str | None): Updated URL.
        rules (str | None): Updated rules.
    """

    game_id: str | None = Field(default=None, description="Updated game ID")
    name: str | None = Field(default=None, description="Updated level name")
    url: str | None = Field(default=None, description="Updated URL")
    rules: str | None = Field(default=None, description="Updated rules")
