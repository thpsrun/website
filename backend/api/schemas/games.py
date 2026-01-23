from datetime import date
from typing import Any

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema, SlugMixin


class GameBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Game` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the game.
        name (str): Full game name (e.g., "Tony Hawk's Pro Skater 4").
        slug (str): URL-friendly abbreviation (e.g., "thps4").
        twitch (str | None): Game name as it appears on Twitch.
        release (date): Game release date.
        boxart (str): URL to game cover art.
        defaulttime (str): Default timing method for full-game runs.
        idefaulttime (str): Default timing method for individual level runs.
        pointsmax (int): Maximum points for world record full-game runs.
        ipointsmax (int): Maximum points for world record IL runs.
    """

    id: str = Field(..., max_length=10, description="Speedrun.com game ID")
    name: str = Field(..., max_length=55, description="Full game name")
    slug: str = Field(..., max_length=20, description="URL-friendly game abbreviation")
    twitch: str | None = Field(
        default=None, max_length=55, description="Game name as it appears on Twitch"
    )
    release: date = Field(..., description="Game release date")
    boxart: str = Field(..., description="URL to game box art/cover image")
    defaulttime: str = Field(
        ...,
        description="Default timing method for full-game runs",
        pattern="^(realtime|realtime_noloads|ingame)$",
    )
    idefaulttime: str = Field(
        ...,
        description="Default timing method for individual level runs",
        pattern="^(realtime|realtime_noloads|ingame)$",
    )
    pointsmax: int = Field(
        1000,
        description="Maximum points awarded for world record full-game runs",
        ge=1,
    )
    ipointsmax: int = Field(
        100,
        description="Maximum points awarded for world record IL runs",
        ge=1,
    )


class GameSchema(GameBaseSchema):
    """Complete game schema with optional embedded data.

    Attributes:
        categories (List[dict] | None): Game categories - included with ?embed=categories.
        levels (List[dict] | None): Individual levels - included with ?embed=levels.
        platforms (List[dict] | None): Supported platforms - included with ?embed=platforms.
    """

    categories: list[dict] | None = Field(
        None,
        description="Game categories (Any%, 100%, etc.)",
    )
    levels: list[dict] | None = Field(
        None,
        description="Individual levels (if applicable)",
    )
    platforms: list[dict] | None = Field(
        None,
        description="Supported platforms for this game",
    )

    @field_validator("platforms", "categories", "levels", mode="before")
    @classmethod
    def convert_manager_to_list(cls, v: Any) -> list[dict] | None:
        """Convert Django ManyRelatedManager or QuerySet to list of dicts."""
        if v is None:
            return None
        # If it's already a list, return as-is
        if isinstance(v, list):
            return v
        # If it's a Django queryset or manager, convert to list
        if hasattr(v, "all"):
            return None  # Return None if not explicitly embedded
        return v


class GameListSchema(BaseEmbedSchema):
    """Schema for paginated game list responses.

    Attributes:
        count (int): Total number of games.
        results (List[GameSchema]): Games for this page.
    """

    count: int = Field(..., description="Total number of games")
    results: list[GameSchema] = Field(..., description="Games for this page")


class GameCreateSchema(BaseEmbedSchema):
    """Schema for creating new games.

    Attributes:
        id (str | None): The game ID; if one is not given, it will auto-generate.
        name (str): Game name.
        slug (str): URL-friendly game abbreviation.
        twitch (str | None): Game name as it appears on Twitch.
        release (date): Game release date.
        boxart (str): URL to game box art/cover image.
        defaulttime (str): Default timing method for full-game runs.
        idefaulttime (str): Default timing method for individual level runs.
        pointsmax (int): Maximum points for world record full-game runs.
        ipointsmax (int): Maximum points for world record individual level runs.
    """

    id: str | None = Field(
        default=None,
        max_length=12,
        description="The game ID; if one is not given, it will auto-generate.",
    )
    name: str = Field(..., max_length=55)
    slug: str = Field(..., max_length=20)
    twitch: str | None = Field(default=None, max_length=55)
    release: date = Field(...)
    boxart: str = Field(...)
    defaulttime: str = Field("realtime", pattern="^(realtime|realtime_noloads|ingame)$")
    idefaulttime: str = Field(
        "realtime", pattern="^(realtime|realtime_noloads|ingame)$"
    )
    pointsmax: int = Field(1000, ge=1)
    ipointsmax: int = Field(100, ge=1)


class GameUpdateSchema(BaseEmbedSchema):
    """Schema for updating existing games.

    This would be used for PUT/PATCH /games/{id} endpoints.

    Attributes:
        name (str | None): Updated game name.
        slug (str | None): Updated URL-friendly game abbreviation.
        twitch (str | None): Updated Twitch name.
        release (date | None): Updated release date.
        boxart (str | None): Updated box art URL.
        defaulttime (str | None): Updated default timing method for full-game runs.
        idefaulttime (str | None): Updated default timing method for IL runs.
        pointsmax (int | None): Updated max points for full-game runs.
        ipointsmax (int | None): Updated max points for IL runs.
    """

    name: str | None = Field(default=None, max_length=55)
    slug: str | None = Field(default=None, max_length=20)
    twitch: str | None = Field(default=None, max_length=55)
    release: date | None = Field(default=None)
    boxart: str | None = Field(default=None)
    defaulttime: str | None = Field(
        None, pattern="^(realtime|realtime_noloads|ingame)$"
    )
    idefaulttime: str | None = Field(
        None, pattern="^(realtime|realtime_noloads|ingame)$"
    )
    pointsmax: int | None = Field(default=None, ge=1)
    ipointsmax: int | None = Field(default=None, ge=1)


GameSchema.model_rebuild()
