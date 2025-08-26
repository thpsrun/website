"""
Streams Schemas for Django Ninja API

Schemas for streaming/live data endpoints. These handle real-time information
about streamers playing speedrun games, current activity, and live statistics.

Key Features:
- Live streaming data integration
- Player streaming status
- Current activity tracking
- Real-time statistics
"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field

from .base import BaseEmbedSchema


class StreamSchema(BaseEmbedSchema):
    """
    Schema for streaming data.

    Represents a player currently streaming speedrun content.

    Attributes:
        player: Player information
        game: Game being played
        title: Stream title
        url: Stream URL
        platform: Streaming platform (Twitch, YouTube, etc.)
        viewers: Current viewer count
        started_at: When stream started
        last_updated: When data was last refreshed
    """

    player: dict = Field(..., description="Player information")
    game: Optional[dict] = Field(None, description="Game being played")
    title: str = Field(..., description="Stream title")
    url: str = Field(..., description="Stream URL")
    platform: str = Field(..., description="Streaming platform")
    viewers: Optional[int] = Field(None, description="Current viewer count", ge=0)
    started_at: Optional[datetime] = Field(None, description="Stream start time")
    last_updated: datetime = Field(..., description="Last data refresh")


class LiveStatsSchema(BaseEmbedSchema):
    """
    Schema for live statistics.

    Provides real-time statistics about speedrunning activity.

    Attributes:
        total_streamers: Total number of active streamers
        total_viewers: Total viewers across all streams
        top_games: Most popular games being streamed
        recent_activity: Recent runs/PBs/WRs
    """

    total_streamers: int = Field(..., description="Total active streamers", ge=0)
    total_viewers: int = Field(..., description="Total viewers", ge=0)
    top_games: List[dict] = Field(..., description="Most popular streamed games")
    recent_activity: List[dict] = Field(..., description="Recent speedrun activity")
    last_updated: datetime = Field(..., description="Last data refresh")
