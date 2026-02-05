from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from api.v1.schemas.base import BaseEmbedSchema, BaseModel


class RunBaseSchemaTimes(BaseModel):
    """Base schema that handles the time"""

    time: str | None = None
    time_secs: float | None = None
    timenl: str | None = None
    timenl_secs: float | None = None
    timeigt: str | None = None
    timeigt_secs: float | None = None


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

    id: str = Field(..., max_length=15)
    runtype: str = Field(
        ..., pattern="^(main|il)$", description="main=full-game, il=individual level"
    )
    place: int = Field(..., ge=0)
    subcategory: str | None = Field(
        default=None,
        max_length=100,
        description="Human-readable subcategory combo",
    )
    time: str | None = Field(
        default=None, max_length=25, description="Formatted (e.g. 1:23.456)"
    )
    time_secs: float | None = Field(
        default=None, ge=0, description="For sorting/calculations"
    )
    video: str | None = None
    date: datetime | None = None
    v_date: datetime | None = Field(default=None, description="Verification date")
    url: str


class RunSchema(RunBaseSchema):
    """Complete run schema with optional embedded data.

    Attributes:
        game (str | dict | None): Game ID (default) or full game info with ?embed=game.
        category (str | dict | None): Category ID (default) or full category info with
            ?embed=category.
        level (str | dict | None): Level ID (default) or full level info with ?embed=level.
        players (List[dict]): All players who participated in this run (always included).
        variables (dict[str, str] | list[dict]): Variable ID:Value ID mapping (default) or
            full variable info with ?embed=variables.
    """

    game: str | dict | None = Field(None, description="ID or embedded with ?embed=game")
    category: str | dict | None = Field(
        None, description="ID or embedded with ?embed=category"
    )
    level: str | dict | None = Field(
        None, description="ID or embedded with ?embed=level"
    )
    players: list[dict] = Field(default_factory=list)
    variables: dict[str, str] | list[dict] = Field(
        default_factory=dict,
        description="ID mapping or embedded with ?embed=variables",
    )
    bonus: int = Field(exclude=True)

    @field_validator("game", "category", "level", mode="before")
    @classmethod
    def convert_model_to_id(
        cls,
        v: Any,
    ) -> str | dict | None:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            return v
        if hasattr(v, "id"):
            return v.id
        return None

    @field_validator("variables", mode="before")
    @classmethod
    def convert_variables_to_mapping(
        cls,
        v: Any,
    ) -> dict[str, str] | list[dict]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            return v
        if hasattr(v, "all"):
            return {}
        return {}

    @field_validator("players", mode="before")
    @classmethod
    def convert_players_manager_to_list(
        cls,
        v: Any,
    ) -> list[dict]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
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
        default=None, max_length=12, description="Auto-generates if omitted"
    )
    game_id: str
    category_id: str | None = None
    level_id: str | None = Field(default=None, description="For IL runs")
    player_ids: list[str] | None = Field(None, description="In order of participation")
    runtype: str = Field(..., pattern="^(main|il)$")
    place: int = Field(..., ge=1)
    subcategory: str | None = Field(default=None, max_length=100)
    time: str | None = Field(default=None, max_length=25)
    time_secs: float | None = Field(default=None, ge=0)
    video: str | None = None
    date: datetime | None = None
    v_date: datetime | None = Field(default=None, description="Verification date")
    url: str
    variable_values: dict[str, str] | None = Field(None)


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

    game_id: str | None = None
    category_id: str | None = None
    level_id: str | None = None
    player_ids: list[str] | None = Field(None, description="In order of participation")
    runtype: str | None = Field(default=None, pattern="^(main|il)$")
    place: int | None = Field(default=None, ge=1)
    subcategory: str | None = Field(default=None, max_length=100)
    time: str | None = Field(default=None, max_length=25)
    time_secs: float | None = Field(default=None, ge=0)
    video: str | None = None
    date: datetime | None = None
    v_date: datetime | None = Field(default=None, description="Verification date")
    url: str | None = None
    variable_values: dict[str, str] | None = None
