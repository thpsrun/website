from typing import List, Optional

from pydantic import Field

from api.schemas.base import BaseEmbedSchema, SlugMixin


class LevelBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Levels` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the level.
        name (str): Level name (e.g., "Warehouse", "School").
        slug (str): URL-friendly version.
        url (str): Link to level on Speedrun.com.
        rules (Optional[str]): Level-specific rules text.
    """

    id: str = Field(..., max_length=10, description="Speedrun.com level ID")
    name: str = Field(..., max_length=75, description="Level name")
    slug: str = Field(..., max_length=75, description="URL-friendly level slug")
    url: str = Field(..., description="Speedrun.com URL for this level")
    rules: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Level-specific rules and requirements",
    )


class LevelSchema(LevelBaseSchema):
    """Complete level schema with optional embedded data.

    Attributes:
        game (Optional[dict]): Game this level belongs to - included with ?embed=game.
        variables (Optional[List[dict]]): Level-specific variables - included with ?embed=variables.
        values (Optional[List[dict]]): Variables with values - included with ?embed=values.
    """

    game: Optional[dict] = Field(None, description="Game this level belongs to")
    variables: Optional[List[dict]] = Field(
        None,
        description="Level-specific variables/subcategories",
    )
    values: Optional[List[dict]] = Field(
        None, description="Variables with their values"
    )


class LevelCreateSchema(BaseEmbedSchema):
    """Schema for creating new levels.

    Attributes:
        game_id (str): Game ID this level belongs to.
        name (str): Level name.
        url (str): Speedrun.com URL.
        rules (Optional[str]): Level-specific rules.
    """

    game_id: str = Field(..., description="ID of the game this level belongs to")
    name: str = Field(..., description="Level name")
    url: str = Field(..., description="Speedrun.com URL")
    rules: Optional[str] = Field(default=None, description="Level-specific rules")


class LevelUpdateSchema(BaseEmbedSchema):
    """Schema for updating levels.

    Attributes:
        game_id (Optional[str]): Updated game ID.
        name (Optional[str]): Updated level name.
        url (Optional[str]): Updated URL.
        rules (Optional[str]): Updated rules.
    """

    game_id: Optional[str] = Field(default=None, description="Updated game ID")
    name: Optional[str] = Field(default=None, description="Updated level name")
    url: Optional[str] = Field(default=None, description="Updated URL")
    rules: Optional[str] = Field(default=None, description="Updated rules")
