from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from api.schemas.base import BaseEmbedSchema


class RunBaseSchema(BaseEmbedSchema):
    """Base schema for `Runs` data without embeds.

    Attributes:
        id (str): Unique ID (usually based on SRC) of the run.
        runtype (str): Whether this is a full-game or individual level run.
        place (int): Leaderboard position.
        subcategory (str | None): Human-readable subcategory description.
        time (str | None): Formatted time string (e.g., "1:23.456").
        time_secs (float | None): Time in seconds (for sorting/calculations).
        video (str | None): Video URL.
        date (datetime | None): Submission date.
        v_date (datetime | None): Verification date.
        url (str): Speedrun.com URL.
    """

    id: str = Field(..., max_length=10, description="Speedrun.com run ID")
    runtype: str = Field(..., description="Run type", pattern="^(main|il)$")
    place: int = Field(..., description="Leaderboard position", ge=0)
    subcategory: str | None = Field(
        default=None,
        max_length=100,
        description="Human-readable subcategory description",
    )
    time: str | None = Field(
        default=None, max_length=25, description="Formatted time string"
    )
    time_secs: float | None = Field(default=None, description="Time in seconds", ge=0)
    video: str | None = Field(default=None, description="Video URL")
    date: datetime | None = Field(default=None, description="Submission date")
    v_date: datetime | None = Field(default=None, description="Verification date")
    url: str = Field(..., description="Speedrun.com URL")


class RunSchema(RunBaseSchema):
    """Complete run schema with optional embedded data.

    Attributes:
        game (dict | None): Game information - included with ?embed=game.
        category (dict | None): Category information - included with ?embed=category.
        level (dict | None): Level information - included with ?embed=level.
        players (List[dict]): All players who participated in this run (always included).
        variables (List[dict] | None): Variable selections - included with ?embed=variables.
    """

    game: dict | None = Field(None, description="Game information")
    category: dict | None = Field(None, description="Category information")
    level: dict | None = Field(None, description="Level information")
    players: list[dict] = Field(
        default_factory=list, description="Players who participated"
    )
    variables: list[dict] | None = Field(None, description="Variable selections")

    @field_validator("game", "category", "level", mode="before")
    @classmethod
    def convert_model_to_none(cls, v: Any) -> dict | None:
        """Convert Django model instance to None if not explicitly embedded."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        # If it's a Django model, return None (embeds will be applied separately)
        return None

    @field_validator("variables", mode="before")
    @classmethod
    def convert_variables_manager_to_none(cls, v: Any) -> list[dict] | None:
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
    def convert_players_manager_to_list(cls, v: Any) -> list[dict]:
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
        id (str | None): The run ID; if one is not given, it will auto-generate.
        game_id (str): Game ID.
        category_id (str | None): Category ID.
        level_id (str | None): Level ID (for ILs).
        player_ids (list[str] | None): List of player IDs in order of participation.
        runtype (str): Run type (main or il).
        place (int): Leaderboard position.
        subcategory (str | None): Human-readable subcategory description.
        time (str | None): Formatted time string.
        time_secs (float | None): Time in seconds.
        video (str | None): Video URL.
        date (datetime | None): Submission date.
        v_date (datetime | None): Verification date.
        url (str): Speedrun.com URL.
        variable_values (dict[str, str] | None): Variable value selections.
    """

    id: str | None = Field(
        default=None,
        max_length=12,
        description="The run ID; if one is not given, it will auto-generate.",
    )
    game_id: str = Field(..., description="Game ID")
    category_id: str | None = Field(default=None, description="Category ID")
    level_id: str | None = Field(default=None, description="Level ID (for ILs)")
    player_ids: list[str] | None = Field(
        None, description="List of player IDs in order of participation"
    )
    runtype: str = Field(..., pattern="^(main|il)$")
    place: int = Field(..., ge=1)
    subcategory: str | None = Field(default=None, max_length=100)
    time: str | None = Field(default=None, max_length=25)
    time_secs: float | None = Field(default=None, ge=0)
    video: str | None = Field(default=None)
    date: datetime | None = Field(default=None)
    v_date: datetime | None = Field(default=None)
    url: str = Field(...)
    # Variable values as a dict: {"variable_id": "value_id"}
    variable_values: dict[str, str] | None = Field(
        None, description="Variable value selections"
    )


class RunUpdateSchema(BaseEmbedSchema):
    """Schema for updating runs.

    Attributes:
        game_id (str | None): Updated game ID.
        category_id (str | None): Updated category ID.
        level_id (str | None): Updated level ID.
        player_ids (list[str] | None): Updated list of player IDs.
        runtype (str | None): Updated run type.
        place (int | None): Updated leaderboard position.
        subcategory (str | None): Updated subcategory description.
        time (str | None): Updated formatted time string.
        time_secs (float | None): Updated time in seconds.
        video (str | None): Updated video URL.
        date (datetime | None): Updated submission date.
        v_date (datetime | None): Updated verification date.
        url (str | None): Updated Speedrun.com URL.
        variable_values (dict[str, str] | None): Updated variable selections.
    """

    game_id: str | None = Field(default=None)
    category_id: str | None = Field(default=None)
    level_id: str | None = Field(default=None)
    player_ids: list[str] | None = Field(
        None, description="List of player IDs in order of participation"
    )
    runtype: str | None = Field(default=None, pattern="^(main|il)$")
    place: int | None = Field(default=None, ge=1)
    subcategory: str | None = Field(default=None, max_length=100)
    time: str | None = Field(default=None, max_length=25)
    time_secs: float | None = Field(default=None, ge=0)
    video: str | None = Field(default=None)
    date: datetime | None = Field(default=None)
    v_date: datetime | None = Field(default=None)
    url: str | None = Field(default=None)
    variable_values: dict[str, str] | None = Field(default=None)
