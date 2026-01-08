"""
Games Schemas for Django Ninja API

This module contains Pydantic schemas for the Games model and related endpoints.
These schemas replace the Django REST Framework GameSerializer and provide:

- Better type safety with full IDE support
- Automatic OpenAPI documentation generation
- Faster validation than DRF serializers
- Cleaner handling of conditional embeds

Schema Design Improvements:
1. **Union Types for Embeds**: Instead of conditionally including/excluding fields
   like DRF serializers, we use Optional[List[Schema]] for embedded data
2. **Type Safety**: All fields are properly typed with validation
3. **Documentation**: Each field has descriptions for auto-generated docs
4. **Performance**: Pydantic validation is significantly faster than DRF

Embed System:
- categories: Include related categories for the game
- levels: Include related levels (individual level runs)
- platforms: Include supported platforms for the game

Example API Usage:
    GET /api/v1/games/thps4 -> Basic game data
    GET /api/v1/games/thps4?embed=categories,platforms -> Game with nested data
    GET /api/v1/games/all?embed=categories -> All games with categories
"""

from datetime import date
from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema, SlugMixin


class GameBaseSchema(SlugMixin, BaseEmbedSchema):
    """
    Base schema for Game data without embeds.

    Contains all the core Game model fields with proper typing.
    This is the minimal representation of a game.

    Attributes:
        id: SRC game ID (primary key)
        name: Full game name (e.g., "Tony Hawk's Pro Skater 4")
        slug: URL-friendly abbreviation (e.g., "thps4")
        twitch: Game name as it appears on Twitch
        release: Game release date
        boxart: URL to game cover art
        defaulttime: Default timing method for full-game runs
        idefaulttime: Default timing method for individual level runs
        pointsmax: Maximum points for world record full-game runs
        ipointsmax: Maximum points for world record IL runs
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
    """
    Complete Game schema with optional embedded data.

    This is the main response schema for game endpoints. It extends the base
    schema to include optional embedded related data based on query parameters.

    The embed system uses Optional[List[Schema]] to handle conditional inclusion:
    - If embed not requested: field will be None
    - If embed requested: field will contain the related data

    This is much cleaner than DRF's approach of conditionally including/excluding
    fields in the to_representation() method.

    Attributes:
        categories (Optional[List[dict]]): Game categories - included with ?embed=categories
        levels (Optional[List[dict]]): Individual levels - included with ?embed=levels
        platforms (Optional[List[dict]]): Supported platforms - included with ?embed=platforms

    Example Responses:
        Basic game (no embeds):
        {
            "id": "n2680o1p",
            "name": "Tony Hawk's Underground",
            "slug": "thug1",
            "categories": null,
            "levels": null,
            "platforms": null
        }

        With categories embed:
        {
            "id": "n2680o1p",
            "name": "Tony Hawk's Underground",
            "categories": [
                {"id": "rklge08d", "name": "Any%", "type": "per-game"},
                {"id": "xklge08d", "name": "100%", "type": "per-game"}
            ],
            "levels": null,
            "platforms": null
        }
    """

    # Optional embedded data - None unless specifically requested via ?embed= parameter
    # Using forward references to avoid circular imports
    categories: Optional[List[dict]] = Field(
        None,
        description="Game categories (Any%, 100%, etc.) - included with ?embed=categories",
    )
    levels: Optional[List[dict]] = Field(
        None,
        description="Individual levels available in this game - included with ?embed=levels",
    )
    platforms: Optional[List[dict]] = Field(
        None,
        description="Supported platforms for this game - included with ?embed=platforms",
    )


class GameListSchema(BaseEmbedSchema):
    """
    Schema for paginated game list responses.

    Used when returning multiple games (e.g., GET /games/all).
    Includes pagination metadata and the games array.

    This provides consistent pagination across all list endpoints,
    which is an improvement over DRF's inconsistent pagination handling.

    Attributes:
        count (int): Total number of games
        results (List[GameSchema]): Games for this page
    """

    count: int = Field(..., description="Total number of games")
    results: List[GameSchema] = Field(..., description="Games for this page")


class GameCreateSchema(BaseEmbedSchema):
    """
    Schema for creating new games.

    This would be used for POST /games endpoints (if implemented).
    Only includes fields that can be set during creation.

    Note: In the current system, games are imported from Speedrun.com
    rather than created manually, so this might not be needed.

    Attributes:
        name (str): Game name
        slug (str): URL-friendly game abbreviation
        twitch (Optional[str]): Game name as it appears on Twitch
        release (date): Game release date
        boxart (str): URL to game box art/cover image
        defaulttime (str): Default timing method for full-game runs
        idefaulttime (str): Default timing method for individual level runs
        pointsmax (int): Maximum points for world record full-game runs
        ipointsmax (int): Maximum points for world record IL runs
    """

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
    """
    Schema for updating existing games.

    This would be used for PUT/PATCH /games/{id} endpoints.
    All fields are optional for partial updates.

    Attributes:
        name (Optional[str]): Updated game name
        slug (Optional[str]): Updated URL-friendly game abbreviation
        twitch (Optional[str]): Updated Twitch name
        release (Optional[date]): Updated release date
        boxart (Optional[str]): Updated box art URL
        defaulttime (Optional[str]): Updated default timing method for full-game runs
        idefaulttime (Optional[str]): Updated default timing method for IL runs
        pointsmax (Optional[int]): Updated max points for full-game runs
        ipointsmax (Optional[int]): Updated max points for IL runs
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


# Forward reference resolution for circular imports
# This is needed because GameSchema references CategorySchema, LevelSchema, etc.
# and those schemas may reference GameSchema back
GameSchema.model_rebuild()
