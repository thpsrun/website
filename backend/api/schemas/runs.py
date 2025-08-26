"""
Runs Schemas for Django Ninja API

Schemas for the Runs model - the core entity representing individual speedruns.
This is one of the most complex schemas due to the many relationships and
the variable subcategory system.

Key Features:
- Game/Category/Level relationships
- Player and Player2 (for co-op runs)
- Variable values (subcategory selections)
- Multiple time formats (RTA, LRT, IGT)
- Status system (verified, new, rejected)
- Points calculation integration
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from .base import BaseEmbedSchema


class RunBaseSchema(BaseEmbedSchema):
    """
    Base run schema without embeds.

    Contains all core run data including times, status, and basic metadata.

    Attributes:
        id: Speedrun.com run ID
        runtype: Whether this is a full-game or individual level run
        place: Leaderboard position
        subcategory: Human-readable subcategory description
        time: Formatted time string (e.g., "1:23.456")
        time_secs: Time in seconds (for sorting/calculations)
        video: Video URL
        date: Submission date
        v_date: Verification date
        status: Verification status
        url: Speedrun.com URL
    """

    id: str = Field(
        ..., max_length=10, description="Speedrun.com run ID", example="y8dwozoj"
    )
    runtype: str = Field(
        ..., description="Run type", example="main", pattern="^(main|il)$"
    )
    place: int = Field(..., description="Leaderboard position", example=1, ge=1)
    subcategory: Optional[str] = Field(
        None, max_length=100, description="Human-readable subcategory description"
    )
    time: Optional[str] = Field(
        None, max_length=25, description="Formatted time string", example="1:23.456"
    )
    time_secs: Optional[float] = Field(
        None, description="Time in seconds", example=83.456, ge=0
    )
    video: Optional[str] = Field(None, description="Video URL")
    date: Optional[datetime] = Field(None, description="Submission date")
    v_date: Optional[datetime] = Field(None, description="Verification date")
    url: str = Field(..., description="Speedrun.com URL")


class RunSchema(RunBaseSchema):
    """
    Complete run schema with optional embedded data.

    Supports embedding related objects like game, category, player, etc.

    Supported Embeds:
        - game: Game information
        - category: Category information
        - level: Level information (for ILs)
        - players: All players who participated in this run
        - variables: Variable values (subcategory selections)
    """

    game: Optional[dict] = Field(
        None, description="Game information - included with ?embed=game"
    )
    category: Optional[dict] = Field(
        None, description="Category information - included with ?embed=category"
    )
    level: Optional[dict] = Field(
        None, description="Level information - included with ?embed=level"
    )
    players: Optional[List[dict]] = Field(
        None, description="Players who participated - included with ?embed=players"
    )
    variables: Optional[List[dict]] = Field(
        None, description="Variable selections - included with ?embed=variables"
    )


class RunCreateSchema(BaseEmbedSchema):
    """Schema for creating runs."""

    game_id: str = Field(..., description="Game ID")
    category_id: Optional[str] = Field(None, description="Category ID")
    level_id: Optional[str] = Field(None, description="Level ID (for ILs)")
    player_ids: Optional[List[str]] = Field(
        None, description="List of player IDs in order of participation"
    )
    runtype: str = Field(..., pattern="^(main|il)$")
    place: int = Field(..., ge=1)
    subcategory: Optional[str] = Field(None, max_length=100)
    time: Optional[str] = Field(None, max_length=25)
    time_secs: Optional[float] = Field(None, ge=0)
    video: Optional[str] = Field(None)
    date: Optional[datetime] = Field(None)
    v_date: Optional[datetime] = Field(None)
    url: str = Field(...)
    # Variable values as a dict: {"variable_id": "value_id"}
    variable_values: Optional[Dict[str, str]] = Field(
        None, description="Variable value selections"
    )


class RunUpdateSchema(BaseEmbedSchema):
    """Schema for updating runs."""

    game_id: Optional[str] = Field(None)
    category_id: Optional[str] = Field(None)
    level_id: Optional[str] = Field(None)
    player_ids: Optional[List[str]] = Field(
        None, description="List of player IDs in order of participation"
    )
    runtype: Optional[str] = Field(None, pattern="^(main|il)$")
    place: Optional[int] = Field(None, ge=1)
    subcategory: Optional[str] = Field(None, max_length=100)
    time: Optional[str] = Field(None, max_length=25)
    time_secs: Optional[float] = Field(None, ge=0)
    video: Optional[str] = Field(None)
    date: Optional[datetime] = Field(None)
    v_date: Optional[datetime] = Field(None)
    url: Optional[str] = Field(None)
    variable_values: Optional[Dict[str, str]] = Field(None)
