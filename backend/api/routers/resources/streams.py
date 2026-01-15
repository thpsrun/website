from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Games, NowStreaming, Players

from api.docs.streams import STREAMS_DELETE, STREAMS_LIVE, STREAMS_POST, STREAMS_PUT
from api.permissions import admin_auth, moderator_auth, public_auth
from api.schemas.base import ErrorResponse
from api.schemas.streams import StreamCreateSchema, StreamSchema, StreamUpdateSchema

router = Router()


def get_mock_streaming_data() -> List[Dict[str, Any]]:
    """
    Mock streaming data for demonstration.

    In production, this would integrate with actual streaming APIs
    like Twitch, YouTube, etc. to get real-time streaming data.

    Returns:
        List of mock streaming data
    """
    # This is demo data - replace with actual API calls
    mock_streams = [
        {
            "player": {"id": "player1", "name": "SpeedRunner123"},
            "game": {"id": "thps4", "name": "Tony Hawk's Pro Skater 4"},
            "title": "Going for Any% WR - Day 47",
            "url": "https://twitch.tv/speedrunner123",
            "platform": "twitch",
            "viewers": 1250,
            "started_at": datetime.now() - timedelta(hours=2),
            "last_updated": datetime.now(),
        },
        {
            "player": {"id": "player2", "name": "THPSMaster"},
            "game": {"id": "thps2", "name": "Tony Hawk's Pro Skater 2"},
            "title": "100% Speedrun Practice",
            "url": "https://twitch.tv/thpsmaster",
            "platform": "twitch",
            "viewers": 834,
            "started_at": datetime.now() - timedelta(minutes=45),
            "last_updated": datetime.now(),
        },
    ]

    return mock_streams


@router.get(
    "/live",
    response=Union[List[StreamSchema], ErrorResponse],
    summary="Get Live Streamers",
    description="""
    Get list of currently live streamers playing speedrun games.

    **Supported Parameters:**
    - `game_id`: Filter by specific game being streamed
    - `platform`: Filter by streaming platform (twitch, youtube, etc.)
    - `min_viewers`: Minimum viewer count
    - `limit`: Maximum results to return (default 20, max 50)

    **Examples:**
    - `/streams/live` - All live streamers
    - `/streams/live?game_id=thps4` - Streamers playing THPS4
    - `/streams/live?min_viewers=100` - Streamers with 100+ viewers

    **Note:** This endpoint provides mock data for demonstration.
    In production, integrate with actual streaming platform APIs.
    """,
    auth=public_auth,
    openapi_extra=STREAMS_LIVE,
)
def get_live_streams(
    request: HttpRequest,
    game_id: Optional[str] = Query(
        None,
        description="Filter by game",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=50,
        description="Max results",
    ),
) -> Union[List[StreamSchema], ErrorResponse]:
    try:
        # TODO: DELETE BEFORE PROD.
        streams_data = get_mock_streaming_data()

        filtered_streams = []
        for stream in streams_data:
            if game_id and stream["game"]:
                if stream["game"]["id"] != game_id:
                    continue

            filtered_streams.append(stream)

        limited_streams = filtered_streams[:limit]

        stream_schemas = []
        for stream_data in limited_streams:
            stream_schema = StreamSchema(**stream_data)
            stream_schemas.append(stream_schema)

        return stream_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve live streams",
            details={"exception": str(e)},
            code=500,
        )


@router.post(
    "/",
    response=Union[StreamSchema, ErrorResponse],
    summary="Create Stream",
    description="""
    Creates a new stream record for a player.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Request Body:**
    - `player_id` (str): Player ID who is streaming.
    - `game_id` (Optional[str]): Game ID being played.
    - `title` (str): Stream title.
    - `offline_ct` (int): Offline counter (minutes since last seen).
    - `stream_time` (Optional[datetime]): Stream start time (ISO format).
    """,
    auth=moderator_auth,
    openapi_extra=STREAMS_POST,
)
def create_stream(
    request: HttpRequest,
    stream_data: StreamCreateSchema,
) -> Union[StreamSchema, ErrorResponse]:
    """Create a new stream for a player."""
    try:
        player = Players.objects.filter(id=stream_data.player_id).first()
        if not player:
            return ErrorResponse(
                error="Player does not exist",
                details=None,
                code=400,
            )

        existing_stream = NowStreaming.objects.filter(streamer=player).first()
        if existing_stream:
            return ErrorResponse(
                error="Player already has an active stream. Use PUT to update it.",
                details=None,
                code=400,
            )

        game = None
        if stream_data.game_id:
            game = Games.objects.filter(id=stream_data.game_id).first()
            if not game:
                return ErrorResponse(
                    error="Game does not exist",
                    details=None,
                    code=400,
                )

        stream = NowStreaming.objects.create(
            streamer=player,
            game=game,
            title=stream_data.title,
            offline_ct=stream_data.offline_ct,
            stream_time=stream_data.stream_time or datetime.now(),
        )

        return StreamSchema.model_validate(stream)

    except Exception as e:
        return ErrorResponse(
            error="Failed to create stream",
            details={"exception": str(e)},
            code=500,
        )


@router.put(
    "/{player_id}",
    response=Union[StreamSchema, ErrorResponse],
    summary="Update Stream",
    description="""
    Updates the stream for a specific player.

    **REQUIRES MODERATOR ACCESS OR HIGHER.**

    **Supported Parameters:**
    - `player_id` (str): Unique ID of the player whose stream is being updated.

    **Request Body:**
    - `game_id` (Optional[str]): Updated game ID being played.
    - `title` (Optional[str]): Updated stream title.
    - `offline_ct` (Optional[int]): Updated offline counter (minutes since last seen).
    - `stream_time` (Optional[datetime]): Updated stream start time (ISO format).
    """,
    auth=moderator_auth,
    openapi_extra=STREAMS_PUT,
)
def update_stream(
    request: HttpRequest,
    player_id: str,
    stream_data: StreamUpdateSchema,
) -> Union[StreamSchema, ErrorResponse]:
    try:
        player = Players.objects.filter(id=player_id).first()
        if not player:
            return ErrorResponse(
                error="Player does not exist",
                details=None,
                code=404,
            )

        stream = NowStreaming.objects.filter(streamer=player).first()
        if not stream:
            return ErrorResponse(
                error="Stream does not exist for this player",
                details=None,
                code=404,
            )

        update_data = stream_data.model_dump(exclude_unset=True)

        if "game_id" in update_data:
            if update_data["game_id"]:
                game = Games.objects.filter(id=update_data["game_id"]).first()
                if not game:
                    return ErrorResponse(
                        error="Game does not exist",
                        details=None,
                        code=400,
                    )
                stream.game = game
            else:
                stream.game = None
            del update_data["game_id"]

        for field, value in update_data.items():
            setattr(stream, field, value)

        stream.save()

        return StreamSchema.model_validate(stream)

    except Exception as e:
        return ErrorResponse(
            error="Failed to update stream",
            details={"exception": str(e)},
            code=500,
        )


@router.delete(
    "/{player_id}",
    response=Union[dict, ErrorResponse],
    summary="Delete Stream",
    description="""
    Deletes the stream for a specific player.

    **REQUIRES ADMIN ACCESS.**

    **Supported Parameters:**
    - `player_id` (str): Unique ID of the player whose stream is being deleted.
    """,
    auth=admin_auth,
    openapi_extra=STREAMS_DELETE,
)
def delete_stream(
    request: HttpRequest,
    player_id: str,
) -> Union[dict, ErrorResponse]:
    try:
        player = Players.objects.filter(id=player_id).first()
        if not player:
            return ErrorResponse(
                error="Player does not exist",
                details=None,
                code=404,
            )

        stream = NowStreaming.objects.filter(streamer=player).first()
        if not stream:
            return ErrorResponse(
                error="Stream does not exist for this player",
                details=None,
                code=404,
            )

        player_name = player.nickname if player.nickname else player.name
        stream.delete()

        return {"message": f"Stream for player '{player_name}' deleted successfully"}

    except Exception as e:
        return ErrorResponse(
            error="Failed to delete stream",
            details={"exception": str(e)},
            code=500,
        )
