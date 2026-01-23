from typing import Any

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema


class PlayerBaseSchema(BaseEmbedSchema):
    """Base schema for `Players` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the player.
        name (str): Player name on Speedrun.com.
        nickname (str | None): Custom nickname override (displayed instead of name).
        url (str): Speedrun.com profile URL.
        pfp (str | None): Profile picture URL.
        pronouns (str | None): Player pronouns.
        twitch (str | None): Twitch channel URL.
        youtube (str | None): YouTube channel URL.
        twitter (str | None): Twitter profile URL.
        bluesky (str | None): Bluesky profile URL.
        ex_stream (bool): Whether player is excluded from streaming features.
    """

    id: str = Field(..., max_length=10, description="Speedrun.com player ID")
    name: str = Field(..., max_length=30, description="Player name on Speedrun.com")
    nickname: str | None = Field(
        default=None,
        max_length=30,
        description="Custom nickname (shown instead of name if provided)",
    )
    url: str = Field(..., description="Speedrun.com profile URL")
    pfp: str | None = Field(
        default=None, max_length=100, description="Profile picture URL"
    )
    pronouns: str | None = Field(
        default=None, max_length=20, description="Player's pronouns"
    )
    twitch: str | None = Field(default=None, description="Twitch channel URL")
    youtube: str | None = Field(default=None, description="YouTube channel URL")
    twitter: str | None = Field(default=None, description="Twitter profile URL")
    bluesky: str | None = Field(default=None, description="Bluesky profile URL")
    ex_stream: bool = Field(
        default=False, description="Whether to exclude from streaming features/bots"
    )


class CountrySchema(BaseEmbedSchema):
    """Simple schema for country codes.

    Attributes:
        id (str): Country code ID.
        name (str): Country name.
    """

    id: str = Field(..., description="Country code ID")
    name: str = Field(..., description="Country name")


class AwardSchema(BaseEmbedSchema):
    """Simple schema for awards.

    Attributes:
        name (str): Award name.
        description (str | None): Award description.
        image (str | None): Award image URL.
    """

    name: str = Field(..., description="Award name")
    description: str | None = Field(default=None, description="Award description")
    image: str | None = Field(default=None, description="Award image URL")


class PlayerRunSchema(BaseEmbedSchema):
    """Schema for run data embedded in player responses.

    Attributes:
        id (str): Run ID.
        game (str | None): Game name.
        category (str | None): Category name.
        level (str | None): Level name (for IL runs).
        place (int | None): Placement on leaderboard.
        time (str | None): Run time.
        date (str | None): Run date (ISO format).
        video (str | None): Video URL.
    """

    id: str = Field(..., description="Run ID")
    game: str | None = Field(default=None, description="Game name")
    category: str | None = Field(default=None, description="Category name")
    level: str | None = Field(default=None, description="Level name (for IL runs)")
    place: int | None = Field(default=None, description="Placement on leaderboard")
    time: str | None = Field(default=None, description="Run time")
    date: str | None = Field(default=None, description="Run date (ISO format)")
    video: str | None = Field(default=None, description="Video URL")


class PlayerSchema(PlayerBaseSchema):
    """Complete player schema with optional embedded data.

    Attributes:
        country (CountrySchema | None): Country information - included with ?embed=country.
        awards (list[AwardSchema] | None): Player earned awards - included with ?embed=awards.
        runs (list[PlayerRunSchema] | None): Recent player runs (limited to 20) - included with
            ?embed=runs.
    """

    country: CountrySchema | None = Field(None, description="Country information")
    awards: list[AwardSchema] | None = Field(None, description="Player earned awards")
    runs: list[PlayerRunSchema] | None = Field(
        None, description="Recent player runs (limited to 20)"
    )

    @field_validator("country", mode="before")
    @classmethod
    def convert_country_to_none(cls, v: Any) -> dict | None:
        """Convert Django model instance to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        return None

    @field_validator("awards", "runs", mode="before")
    @classmethod
    def convert_manager_to_none(cls, v: Any) -> list[dict] | None:
        """Convert Django ManyRelatedManager to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if hasattr(v, "all"):
            return None
        return v


class PlayerCreateSchema(BaseEmbedSchema):
    """Schema for creating new players.

    Attributes:
        id (str | None): The player ID; if one is not given, it will auto-generate.
        name (str): Player name.
        nickname (str | None): Custom nickname.
        url (str): Speedrun.com profile URL.
        country_id (str | None): Country code ID.
        pfp (str | None): Profile picture URL.
        pronouns (str | None): Player pronouns.
        twitch (str | None): Twitch channel URL.
        youtube (str | None): YouTube channel URL.
        twitter (str | None): Twitter profile URL.
        bluesky (str | None): Bluesky profile URL.
        ex_stream (bool): Whether to exclude from streaming features.
    """

    id: str | None = Field(
        default=None,
        max_length=12,
        description="The player ID; if one is not given, it will auto-generate.",
    )
    name: str = Field(..., max_length=30)
    nickname: str | None = Field(default=None, max_length=30)
    url: str = Field(...)
    country_id: str | None = Field(default=None, description="Country code ID")
    pfp: str | None = Field(default=None, max_length=100)
    pronouns: str | None = Field(default=None, max_length=20)
    twitch: str | None = Field(default=None)
    youtube: str | None = Field(default=None)
    twitter: str | None = Field(default=None)
    bluesky: str | None = Field(default=None)
    ex_stream: bool = Field(default=False)


class PlayerUpdateSchema(BaseEmbedSchema):
    """Schema for updating players.

    Attributes:
        name (str | None): Updated player name.
        nickname (str | None): Updated nickname.
        url (str | None): Updated Speedrun.com profile URL.
        country_id (str | None): Updated country code ID.
        pfp (str | None): Updated profile picture URL.
        pronouns (str | None): Updated pronouns.
        twitch (str | None): Updated Twitch channel URL.
        youtube (str | None): Updated YouTube channel URL.
        twitter (str | None): Updated Twitter profile URL.
        bluesky (str | None): Updated Bluesky profile URL.
        ex_stream (bool | None): Updated streaming exclusion flag.
    """

    name: str | None = Field(default=None, max_length=30)
    nickname: str | None = Field(default=None, max_length=30)
    url: str | None = Field(default=None)
    country_id: str | None = Field(default=None)
    pfp: str | None = Field(default=None, max_length=100)
    pronouns: str | None = Field(default=None, max_length=20)
    twitch: str | None = Field(default=None)
    youtube: str | None = Field(default=None)
    twitter: str | None = Field(default=None)
    bluesky: str | None = Field(default=None)
    ex_stream: bool | None = Field(default=None)
