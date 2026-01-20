from datetime import date
from typing import Any, List, Optional

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema, SlugMixin


class GameBaseSchema(SlugMixin, BaseEmbedSchema):
    """Base schema for `Game` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the game.
        name (str): Full game name (e.g., "Tony Hawk's Pro Skater 4").
        slug (str): URL-friendly abbreviation (e.g., "thps4").
        twitch (Optional[str]): Game name as it appears on Twitch.
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
    twitch: Optional[str] = Field(
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
        categories (Optional[List[dict]]): Game categories - included with ?embed=categories.
        levels (Optional[List[dict]]): Individual levels - included with ?embed=levels.
        platforms (Optional[List[dict]]): Supported platforms - included with ?embed=platforms.
    """

    categories: Optional[List[dict]] = Field(
        None,
        description="Game categories (Any%, 100%, etc.)",
    )
    levels: Optional[List[dict]] = Field(
        None,
        description="Individual levels (if applicable)",
    )
    platforms: Optional[List[dict]] = Field(
        None,
        description="Supported platforms for this game",
    )

    @field_validator("platforms", "categories", "levels", mode="before")
    @classmethod
    def convert_manager_to_list(cls, v: Any) -> Optional[List[dict]]:
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
    results: List[GameSchema] = Field(..., description="Games for this page")


class GameCreateSchema(BaseEmbedSchema):
    """Schema for creating new games.

    Attributes:
        id (Optional[str]): The game ID; if one is not given, it will auto-generate.
        name (str): Game name.
        slug (str): URL-friendly game abbreviation.
        twitch (Optional[str]): Game name as it appears on Twitch.
        release (date): Game release date.
        boxart (str): URL to game box art/cover image.
        defaulttime (str): Default timing method for full-game runs.
        idefaulttime (str): Default timing method for individual level runs.
        pointsmax (int): Maximum points for world record full-game runs.
        ipointsmax (int): Maximum points for world record individual level runs.
    """

    id: Optional[str] = Field(
        default=None,
        max_length=12,
        description="The game ID; if one is not given, it will auto-generate.",
    )
    name: str = Field(..., max_length=55)
    slug: str = Field(..., max_length=20)
    twitch: Optional[str] = Field(default=None, max_length=55)
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
        name (Optional[str]): Updated game name.
        slug (Optional[str]): Updated URL-friendly game abbreviation.
        twitch (Optional[str]): Updated Twitch name.
        release (Optional[date]): Updated release date.
        boxart (Optional[str]): Updated box art URL.
        defaulttime (Optional[str]): Updated default timing method for full-game runs.
        idefaulttime (Optional[str]): Updated default timing method for IL runs.
        pointsmax (Optional[int]): Updated max points for full-game runs.
        ipointsmax (Optional[int]): Updated max points for IL runs.
    """

    name: Optional[str] = Field(default=None, max_length=55)
    slug: Optional[str] = Field(default=None, max_length=20)
    twitch: Optional[str] = Field(default=None, max_length=55)
    release: Optional[date] = Field(default=None)
    boxart: Optional[str] = Field(default=None)
    defaulttime: Optional[str] = Field(
        None, pattern="^(realtime|realtime_noloads|ingame)$"
    )
    idefaulttime: Optional[str] = Field(
        None, pattern="^(realtime|realtime_noloads|ingame)$"
    )
    pointsmax: Optional[int] = Field(default=None, ge=1)
    ipointsmax: Optional[int] = Field(default=None, ge=1)


GameSchema.model_rebuild()
