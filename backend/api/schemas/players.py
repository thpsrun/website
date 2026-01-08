from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema


class PlayerBaseSchema(BaseEmbedSchema):
    """
    Base player schema without embeds.

    Contains core player information including social links
    and profile customization options.

    Attributes:
        id (str): Speedrun.com player ID
        name (str): Player's name on Speedrun.com
        nickname (Optional[str]): Custom nickname override (displayed instead of name)
        url (str): Speedrun.com profile URL
        pfp (Optional[str]): Profile picture URL
        pronouns (Optional[str]): Player's pronouns
        twitch (Optional[str]): Twitch channel URL
        youtube (Optional[str]): YouTube channel URL
        twitter (Optional[str]): Twitter profile URL
        bluesky (Optional[str]): Bluesky profile URL
        ex_stream (bool): Whether to exclude from streaming features
    """

    id: str = Field(..., max_length=10, description="Speedrun.com player ID")
    name: str = Field(..., max_length=30, description="Player name on Speedrun.com")
    nickname: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Custom nickname (shown instead of name if provided)",
    )
    url: str = Field(..., description="Speedrun.com profile URL")
    pfp: Optional[str] = Field(
        default=None, max_length=100, description="Profile picture URL"
    )
    pronouns: Optional[str] = Field(
        default=None, max_length=20, description="Player's pronouns"
    )
    twitch: Optional[str] = Field(default=None, description="Twitch channel URL")
    youtube: Optional[str] = Field(default=None, description="YouTube channel URL")
    twitter: Optional[str] = Field(default=None, description="Twitter profile URL")
    bluesky: Optional[str] = Field(default=None, description="Bluesky profile URL")
    ex_stream: bool = Field(
        default=False, description="Whether to exclude from streaming features/bots"
    )


class CountrySchema(BaseEmbedSchema):
    """
    Simple schema for country codes.

    Attributes:
        id (str): Country code ID
        name (str): Country name
    """

    id: str = Field(..., description="Country code ID")
    name: str = Field(..., description="Country name")


class AwardSchema(BaseEmbedSchema):
    """
    Simple schema for awards.

    Attributes:
        name (str): Award name
        description (Optional[str]): Award description
        image (Optional[str]): Award image URL
    """

    name: str = Field(..., description="Award name")
    description: Optional[str] = Field(default=None, description="Award description")
    image: Optional[str] = Field(default=None, description="Award image URL")


class PlayerRunSchema(BaseEmbedSchema):
    """
    Schema for run data embedded in player responses.

    Attributes:
        id (str): Run ID
        game (Optional[str]): Game name
        category (Optional[str]): Category name
        level (Optional[str]): Level name (for IL runs)
        place (Optional[int]): Placement on leaderboard
        time (Optional[str]): Run time
        date (Optional[str]): Run date (ISO format)
        video (Optional[str]): Video URL
    """

    id: str = Field(..., description="Run ID")
    game: Optional[str] = Field(default=None, description="Game name")
    category: Optional[str] = Field(default=None, description="Category name")
    level: Optional[str] = Field(default=None, description="Level name (for IL runs)")
    place: Optional[int] = Field(default=None, description="Placement on leaderboard")
    time: Optional[str] = Field(default=None, description="Run time")
    date: Optional[str] = Field(default=None, description="Run date (ISO format)")
    video: Optional[str] = Field(default=None, description="Video URL")


class PlayerSchema(PlayerBaseSchema):
    """
    Complete player schema with optional embedded data.

    Extends base schema to include optional country and awards data.

    Attributes:
        country (Optional[CountrySchema]): Country information - included with ?embed=country
        awards (Optional[List[AwardSchema]]): Player's earned awards - included with ?embed=awards
        runs (Optional[List[PlayerRunSchema]]): Recent player runs - included with ?embed=runs (limited to 20)
    """

    country: Optional[CountrySchema] = Field(
        None, description="Country information - included with ?embed=country"
    )
    awards: Optional[List[AwardSchema]] = Field(
        None, description="Player's earned awards - included with ?embed=awards"
    )
    runs: Optional[List[PlayerRunSchema]] = Field(
        None,
        description="Recent player runs - included with ?embed=runs (limited to 20)",
    )


class PlayerCreateSchema(BaseEmbedSchema):
    """
    Schema for creating new players.

    Attributes:
        name (str): Player name
        nickname (Optional[str]): Custom nickname
        url (str): Speedrun.com profile URL
        country_id (Optional[str]): Country code ID
        pfp (Optional[str]): Profile picture URL
        pronouns (Optional[str]): Player's pronouns
        twitch (Optional[str]): Twitch channel URL
        youtube (Optional[str]): YouTube channel URL
        twitter (Optional[str]): Twitter profile URL
        bluesky (Optional[str]): Bluesky profile URL
        ex_stream (bool): Whether to exclude from streaming features
    """

    name: str = Field(..., max_length=30)
    nickname: Optional[str] = Field(default=None, max_length=30)
    url: str = Field(...)
    country_id: Optional[str] = Field(default=None, description="Country code ID")
    pfp: Optional[str] = Field(default=None, max_length=100)
    pronouns: Optional[str] = Field(default=None, max_length=20)
    twitch: Optional[str] = Field(default=None)
    youtube: Optional[str] = Field(default=None)
    twitter: Optional[str] = Field(default=None)
    bluesky: Optional[str] = Field(default=None)
    ex_stream: bool = Field(default=False)


class PlayerUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating players.

    Attributes:
        name (Optional[str]): Updated player name
        nickname (Optional[str]): Updated nickname
        url (Optional[str]): Updated Speedrun.com profile URL
        country_id (Optional[str]): Updated country code ID
        pfp (Optional[str]): Updated profile picture URL
        pronouns (Optional[str]): Updated pronouns
        twitch (Optional[str]): Updated Twitch channel URL
        youtube (Optional[str]): Updated YouTube channel URL
        twitter (Optional[str]): Updated Twitter profile URL
        bluesky (Optional[str]): Updated Bluesky profile URL
        ex_stream (Optional[bool]): Updated streaming exclusion flag
    """

    name: Optional[str] = Field(default=None, max_length=30)
    nickname: Optional[str] = Field(default=None, max_length=30)
    url: Optional[str] = Field(default=None)
    country_id: Optional[str] = Field(default=None)
    pfp: Optional[str] = Field(default=None, max_length=100)
    pronouns: Optional[str] = Field(default=None, max_length=20)
    twitch: Optional[str] = Field(default=None)
    youtube: Optional[str] = Field(default=None)
    twitter: Optional[str] = Field(default=None)
    bluesky: Optional[str] = Field(default=None)
    ex_stream: Optional[bool] = Field(default=None)
