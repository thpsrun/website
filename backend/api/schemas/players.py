"""
Players Schemas for Django Ninja API

Schemas for the Players model. Players represent speedrunners with
their profiles, social links, awards, and country information.

Key Features:
- Country code relationship
- Awards many-to-many relationship
- Social media links (Twitch, YouTube, Twitter, Bluesky)
- Stream exception handling
- Profile customization (nickname override)
"""

from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema


class PlayerBaseSchema(BaseEmbedSchema):
    """
    Base player schema without embeds.

    Contains core player information including social links
    and profile customization options.

    Attributes:
        id: Speedrun.com player ID
        name: Player's name on Speedrun.com
        nickname: Custom nickname override (displayed instead of name)
        url: Speedrun.com profile URL
        pfp: Profile picture URL
        pronouns: Player's pronouns
        social_links: Various social media platforms
        ex_stream: Whether to exclude from streaming features
    """

    id: str = Field(
        ..., max_length=10, description="Speedrun.com player ID", example="v8lponvj"
    )
    name: str = Field(
        ...,
        max_length=30,
        description="Player name on Speedrun.com",
        example="ThePackle",
    )
    nickname: Optional[str] = Field(
        None,
        max_length=30,
        description="Custom nickname (shown instead of name if provided)",
    )
    url: str = Field(
        ...,
        description="Speedrun.com profile URL",
        example="https://www.speedrun.com/users/ThePackle",
    )
    pfp: Optional[str] = Field(None, max_length=100, description="Profile picture URL")
    pronouns: Optional[str] = Field(
        None, max_length=20, description="Player's pronouns", example="he/him"
    )
    twitch: Optional[str] = Field(None, description="Twitch channel URL")
    youtube: Optional[str] = Field(None, description="YouTube channel URL")
    twitter: Optional[str] = Field(None, description="Twitter profile URL")
    bluesky: Optional[str] = Field(None, description="Bluesky profile URL")
    ex_stream: bool = Field(
        False, description="Whether to exclude from streaming features/bots"
    )


class PlayerSchema(PlayerBaseSchema):
    """
    Complete player schema with optional embedded data.

    Extends base schema to include optional country and awards data.

    Supported Embeds:
        - country: Include country information
        - awards: Include earned awards
        - runs: Include player's runs (limited for performance)
    """

    country: Optional[dict] = Field(
        None, description="Country information - included with ?embed=country"
    )
    awards: Optional[List[dict]] = Field(
        None, description="Player's earned awards - included with ?embed=awards"
    )
    runs: Optional[List[dict]] = Field(
        None,
        description="Recent player runs - included with ?embed=runs (limited to 20)",
    )


class PlayerCreateSchema(BaseEmbedSchema):
    """Schema for creating new players."""

    name: str = Field(..., max_length=30)
    nickname: Optional[str] = Field(None, max_length=30)
    url: str = Field(...)
    country_id: Optional[str] = Field(None, description="Country code ID")
    pfp: Optional[str] = Field(None, max_length=100)
    pronouns: Optional[str] = Field(None, max_length=20)
    twitch: Optional[str] = Field(None)
    youtube: Optional[str] = Field(None)
    twitter: Optional[str] = Field(None)
    bluesky: Optional[str] = Field(None)
    ex_stream: bool = Field(False)


class PlayerUpdateSchema(BaseEmbedSchema):
    """Schema for updating players."""

    name: Optional[str] = Field(None, max_length=30)
    nickname: Optional[str] = Field(None, max_length=30)
    url: Optional[str] = Field(None)
    country_id: Optional[str] = Field(None)
    pfp: Optional[str] = Field(None, max_length=100)
    pronouns: Optional[str] = Field(None, max_length=20)
    twitch: Optional[str] = Field(None)
    youtube: Optional[str] = Field(None)
    twitter: Optional[str] = Field(None)
    bluesky: Optional[str] = Field(None)
    ex_stream: Optional[bool] = Field(None)


class CountrySchema(BaseEmbedSchema):
    """Simple schema for country codes."""

    id: str = Field(..., description="Country code ID")
    name: str = Field(..., description="Country name")


class AwardSchema(BaseEmbedSchema):
    """Simple schema for awards."""

    name: str = Field(..., description="Award name")
    description: Optional[str] = Field(None, description="Award description")
    image: Optional[str] = Field(None, description="Award image URL")
