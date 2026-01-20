from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

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
    place: int = Field(..., description="Leaderboard position", ge=0)
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
        players (List[dict]): All players who participated in this run (always included).
        variables (Optional[List[dict]]): Variable selections - included with ?embed=variables.
    """

    game: Optional[dict] = Field(None, description="Game information")
    category: Optional[dict] = Field(None, description="Category information")
    level: Optional[dict] = Field(None, description="Level information")
    players: List[dict] = Field(default_factory=list, description="Players who participated")
    variables: Optional[List[dict]] = Field(None, description="Variable selections")

    @field_validator("game", "category", "level", mode="before")
    @classmethod
    def convert_model_to_none(cls, v: Any) -> Optional[dict]:
        """Convert Django model instance to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # If it's a Django model, return None (embeds will be applied separately)
        return None

    @field_validator("variables", mode="before")
    @classmethod
    def convert_variables_manager_to_none(cls, v: Any) -> Optional[List[dict]]:
        """Convert Django ManyRelatedManager to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        # If it's a Django manager, return None (embeds will be applied separately)
        if hasattr(v, "all"):
            return None
        return v

    @field_validator("players", mode="before")
    @classmethod
    def convert_players_manager_to_list(cls, v: Any) -> List[dict]:
        """Convert Django ManyRelatedManager to empty list."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # If it's a Django manager, return empty list (will be populated by router)
        if hasattr(v, "all"):
            return []
        return []


class RunCreateSchema(BaseEmbedSchema):
    """Schema for creating runs.

    Attributes:
        id (Optional[str]): The run ID; if one is not given, it will auto-generate.
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

    id: Optional[str] = Field(
        default=None,
        max_length=12,
        description="The run ID; if one is not given, it will auto-generate.",
    )
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
