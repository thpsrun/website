from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from api.schemas.base import BaseEmbedSchema


class RunBaseSchema(BaseEmbedSchema):
    """Base schema for `Runs` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the run.
        runtype (str): Whether this is a full-game or individual level run.
        place (int): Leaderboard position.
        subcategory (Optional[str]): Human-readable subcategory description.
        time (Optional[str]): Formatted time string (e.g., "1:23.456").
        time_secs (Optional[float]): Time in seconds (for sorting/calculations).
        video (Optional[str]): Video URL.
        date (Optional[datetime]): Submission date.
        v_date (Optional[datetime]): Verification date.
        url (str): Speedrun.com URL.
    """

    id: str = Field(..., max_length=10, description="Speedrun.com run ID")
    runtype: str = Field(..., description="Run type", pattern="^(main|il)$")
    place: int = Field(..., description="Leaderboard position", ge=1)
    subcategory: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Human-readable subcategory description",
    )
    time: Optional[str] = Field(
        default=None, max_length=25, description="Formatted time string"
    )
    time_secs: Optional[float] = Field(
        default=None, description="Time in seconds", ge=0
    )
    video: Optional[str] = Field(default=None, description="Video URL")
    date: Optional[datetime] = Field(default=None, description="Submission date")
    v_date: Optional[datetime] = Field(default=None, description="Verification date")
    url: str = Field(..., description="Speedrun.com URL")


class RunSchema(RunBaseSchema):
    """Complete run schema with optional embedded data.

    Attributes:
        game (Optional[dict]): Game information - included with ?embed=game.
        category (Optional[dict]): Category information - included with ?embed=category.
        level (Optional[dict]): Level information - included with ?embed=level.
        players (Optional[List[dict]]): Players who participated - included with ?embed=players.
        variables (Optional[List[dict]]): Variable selections - included with ?embed=variables.
    """

    game: Optional[dict] = Field(None, description="Game information")
    category: Optional[dict] = Field(None, description="Category information")
    level: Optional[dict] = Field(None, description="Level information")
    players: Optional[List[dict]] = Field(None, description="Players who participated")
    variables: Optional[List[dict]] = Field(None, description="Variable selections")


class RunCreateSchema(BaseEmbedSchema):
    """Schema for creating runs.

    Attributes:
        game_id (str): Game ID.
        category_id (Optional[str]): Category ID.
        level_id (Optional[str]): Level ID (for ILs).
        player_ids (Optional[List[str]]): List of player IDs in order of participation.
        runtype (str): Run type (main or il).
        place (int): Leaderboard position.
        subcategory (Optional[str]): Human-readable subcategory description.
        time (Optional[str]): Formatted time string.
        time_secs (Optional[float]): Time in seconds.
        video (Optional[str]): Video URL.
        date (Optional[datetime]): Submission date.
        v_date (Optional[datetime]): Verification date.
        url (str): Speedrun.com URL.
        variable_values (Optional[Dict[str, str]]): Variable value selections.
    """

    game_id: str = Field(..., description="Game ID")
    category_id: Optional[str] = Field(default=None, description="Category ID")
    level_id: Optional[str] = Field(default=None, description="Level ID (for ILs)")
    player_ids: Optional[List[str]] = Field(
        None, description="List of player IDs in order of participation"
    )
    runtype: str = Field(..., pattern="^(main|il)$")
    place: int = Field(..., ge=1)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    time: Optional[str] = Field(default=None, max_length=25)
    time_secs: Optional[float] = Field(default=None, ge=0)
    video: Optional[str] = Field(default=None)
    date: Optional[datetime] = Field(default=None)
    v_date: Optional[datetime] = Field(default=None)
    url: str = Field(...)
    # Variable values as a dict: {"variable_id": "value_id"}
    variable_values: Optional[Dict[str, str]] = Field(
        None, description="Variable value selections"
    )


class RunUpdateSchema(BaseEmbedSchema):
    """Schema for updating runs.

    Attributes:
        game_id (Optional[str]): Updated game ID.
        category_id (Optional[str]): Updated category ID.
        level_id (Optional[str]): Updated level ID.
        player_ids (Optional[List[str]]): Updated list of player IDs.
        runtype (Optional[str]): Updated run type.
        place (Optional[int]): Updated leaderboard position.
        subcategory (Optional[str]): Updated subcategory description.
        time (Optional[str]): Updated formatted time string.
        time_secs (Optional[float]): Updated time in seconds.
        video (Optional[str]): Updated video URL.
        date (Optional[datetime]): Updated submission date.
        v_date (Optional[datetime]): Updated verification date.
        url (Optional[str]): Updated Speedrun.com URL.
        variable_values (Optional[Dict[str, str]]): Updated variable selections.
    """

    game_id: Optional[str] = Field(default=None)
    category_id: Optional[str] = Field(default=None)
    level_id: Optional[str] = Field(default=None)
    player_ids: Optional[List[str]] = Field(
        None, description="List of player IDs in order of participation"
    )
    runtype: Optional[str] = Field(default=None, pattern="^(main|il)$")
    place: Optional[int] = Field(default=None, ge=1)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    time: Optional[str] = Field(default=None, max_length=25)
    time_secs: Optional[float] = Field(default=None, ge=0)
    video: Optional[str] = Field(default=None)
    date: Optional[datetime] = Field(default=None)
    v_date: Optional[datetime] = Field(default=None)
    url: Optional[str] = Field(default=None)
    variable_values: Optional[Dict[str, str]] = Field(default=None)
