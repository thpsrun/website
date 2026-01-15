from datetime import datetime
from typing import Any, Optional

from pydantic import Field, model_validator

from api.schemas.base import BaseEmbedSchema


class StreamSchema(BaseEmbedSchema):
    """Base schema for `Streams` data without embeds.

    Attributes:
        player (dict): Player information from the Players model.
        game (Optional[dict]): Game being played.
        title (str): Stream title.
        offline_ct (int): Minutes since last seen online.
        stream_time (Optional[datetime]): When the stream started.
    """

    player: dict = Field(..., description="Player information from the Players model")
    game: Optional[dict] = Field(default=None, description="Game being played")
    title: str = Field(..., description="Stream title", max_length=100)
    offline_ct: int = Field(
        ..., description="Amount of minutes since last seen online", ge=0
    )
    stream_time: Optional[datetime] = Field(
        default=None, description="Stream start time"
    )

    @model_validator(mode="before")
    @classmethod
    def transform_nowstreaming_model(cls, data: Any) -> Any:
        """Transform NowStreaming model instance to expected schema format.

        The NowStreaming model uses "streamer" as the FK field, but this schema
        expects "player". This validator handles the transformation and creates
        the nested {id, name} dicts for player and game.
        """
        if hasattr(data, "streamer"):
            streamer = data.streamer
            game = data.game
            return {
                "player": {
                    "id": streamer.id,
                    "name": streamer.nickname if streamer.nickname else streamer.name,
                },
                "game": ({"id": game.id, "name": game.name} if game else None),
                "title": data.title,
                "offline_ct": data.offline_ct,
                "stream_time": data.stream_time,
            }
        return data


class StreamCreateSchema(BaseEmbedSchema):
    """Schema for creating streams.

    Attributes:
        player_id (str): Player ID who is streaming.
        game_id (Optional[str]): Game ID being played.
        title (str): Stream title.
        offline_ct (int): Offline counter (minutes since last seen).
        stream_time (Optional[datetime]): Stream start time.
    """

    player_id: str = Field(..., description="Player ID who is streaming")
    game_id: Optional[str] = Field(default=None, description="Game ID being played")
    title: str = Field(..., description="Stream title")
    offline_ct: int = Field(default=0, description="Offline counter (minutes)", ge=0)
    stream_time: Optional[datetime] = Field(
        default=None, description="Stream start time"
    )


class StreamUpdateSchema(BaseEmbedSchema):
    """Schema for updating streams.

    Attributes:
        game_id (Optional[str]): Updated game ID being played.
        title (Optional[str]): Updated stream title.
        offline_ct (Optional[int]): Updated offline counter (minutes since last seen).
        stream_time (Optional[datetime]): Updated stream start time.
    """

    game_id: Optional[str] = Field(default=None, description="Game ID being played")
    title: Optional[str] = Field(default=None, description="Stream title")
    offline_ct: Optional[int] = Field(
        default=None, description="Offline counter (minutes)", ge=0
    )
    stream_time: Optional[datetime] = Field(
        default=None, description="Stream start time"
    )
