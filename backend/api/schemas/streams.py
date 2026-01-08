from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseEmbedSchema


class StreamSchema(BaseEmbedSchema):
    """
    Schema for streaming data.

    Represents a player currently streaming speedrun content.

    Attributes:
        player (dict): Player information from the Players model
        game (Optional[dict]): Game being played
        title (str): Stream title
        offline_ct (int): Amount of minutes since last seen online
        stream_time (Optional[datetime]): When the stream started
    """

    player: dict = Field(..., description="Player information from the Players model")
    game: Optional[dict] = Field(default=None, description="Game being played")
    title: str = Field(..., description="Stream title", max_length=100)
    offline_ct: int = Field(
        ..., description="Amount of minutes since last seen online", ge=0
    )
    stream_time: Optional[datetime] = Field(default=None, description="Stream start time")


class StreamCreateSchema(BaseEmbedSchema):
    """
    Schema for creating streams.

    Used for POST /streams endpoints to create a new stream entry.

    Attributes:
        player_id (str): Player ID who is streaming
        game_id (Optional[str]): Game ID being played
        title (str): Stream title
        offline_ct (int): Offline counter (minutes since last seen)
        stream_time (Optional[datetime]): Stream start time
    """

    player_id: str = Field(..., description="Player ID who is streaming")
    game_id: Optional[str] = Field(default=None, description="Game ID being played")
    title: str = Field(..., description="Stream title")
    offline_ct: int = Field(default=0, description="Offline counter (minutes)", ge=0)
    stream_time: Optional[datetime] = Field(
        default=None, description="Stream start time"
    )


class StreamUpdateSchema(BaseEmbedSchema):
    """
    Schema for updating streams.

    Used for PUT/PATCH /streams/{player_id} endpoints.
    All fields optional for partial updates.

    Attributes:
        game_id (Optional[str]): Game ID being played
        title (Optional[str]): Stream title
        offline_ct (Optional[int]): Offline counter (minutes since last seen)
        stream_time (Optional[datetime]): Stream start time
    """

    game_id: Optional[str] = Field(default=None, description="Game ID being played")
    title: Optional[str] = Field(default=None, description="Stream title")
    offline_ct: Optional[int] = Field(
        None, description="Offline counter (minutes)", ge=0
    )
    stream_time: Optional[datetime] = Field(default=None, description="Stream start time")
