from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from django.http import HttpRequest
from ninja import Query, Router
from srl.models import Games, NowStreaming, Players

from api.auth.api_key import api_admin_check, api_moderator_check, read_only_auth
from api.schemas.base import ErrorResponse
from api.schemas.streams import StreamCreateSchema, StreamSchema, StreamUpdateSchema

router = Router()

# START OPENAPI DOCUMENTATION #
STREAMS_LIVE = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "player": {"id": "player1", "name": "SpeedRunner123"},
                            "game": {"id": "thps4", "name": "Tony Hawk's Pro Skater 4"},
                            "title": "WRWRWRWRWRWRWR",
                            "url": "https://twitch.tv/speedrunner123",
                            "started_at": "2025-08-15T08:30:00Z",
                        },
                        {
                            "player": {"id": "player2", "name": "THPS Man"},
                            "game": {"id": "thps2", "name": "Tony Hawk's Pro Skater 2"},
                            "title": "Practice",
                            "url": "https://twitch.tv/thpsman",
                            "started_at": "2025-08-15T09:45:00Z",
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "query",
            "example": "thps4",
            "schema": {"type": "string"},
            "description": "Filter by game",
        },
        {
            "name": "limit",
            "in": "query",
            "example": 20,
            "schema": {"type": "integer", "minimum": 1, "maximum": 50},
            "description": "Max results (default 20, max 50)",
        },
    ],
}

STREAMS_GAME = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "player": {"id": "player1", "name": "SpeedRunner123"},
                            "game": {"id": "thps4", "name": "Tony Hawk's Pro Skater 4"},
                            "title": "WRWRWRWRWRWRWRWRWR",
                            "url": "https://twitch.tv/speedrunner123",
                            "started_at": "2025-08-15T08:30:00Z",
                        }
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Game not found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "path",
            "required": True,
            "example": "thps4",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Game ID or slug",
        },
        {
            "name": "limit",
            "in": "query",
            "example": 10,
            "schema": {"type": "integer", "minimum": 1, "maximum": 25},
            "description": "Max results (default 10, max 25)",
        },
    ],
}

STREAMS_PLAYER = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "player": {
                            "id": "v8lponvj",
                            "name": "ThePackle",
                            "twitch": "https://twitch.tv/thepackle",
                            "youtube": "https://youtube.com/thepackle",
                        },
                        "is_live": True,
                        "current_stream": {
                            "player": {"id": "v8lponvj", "name": "ThePackle"},
                            "game": {"id": "thps4", "name": "Tony Hawk's Pro Skater 4"},
                            "title": "Any% WR",
                            "url": "https://twitch.tv/thepackle",
                            "started_at": "2025-08-15T08:30:00Z",
                        },
                        "ex_stream": False,
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Player not found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "player_id",
            "in": "path",
            "required": True,
            "example": "v8lponvj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Player ID",
        },
    ],
}

STREAMS_POST = {
    "responses": {
        201: {
            "description": "Stream created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "player": {"id": "v8lponvj", "name": "ThePackle"},
                        "game": {"id": "n2680o1p", "name": "Tony Hawk's Pro Skater 4"},
                        "title": "Going for Any% WR",
                        "offline_ct": 0,
                        "stream_time": "2025-08-15T08:30:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or player/game does not exist."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["player_id", "title"],
                    "properties": {
                        "player_id": {
                            "type": "string",
                            "example": "v8lponvj",
                            "description": "PLAYER ID WHO IS STREAMING",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "GAME ID BEING PLAYED (OPTIONAL)",
                        },
                        "title": {
                            "type": "string",
                            "example": "Going for Any% WR",
                            "description": "STREAM TITLE",
                        },
                        "offline_ct": {
                            "type": "integer",
                            "example": 0,
                            "description": "OFFLINE COUNTER (DEFAULT 0)",
                        },
                        "stream_time": {
                            "type": "string",
                            "format": "date-time",
                            "example": "2025-08-15T08:30:00Z",
                            "description": "STREAM START TIME (OPTIONAL)",
                        },
                    },
                },
                "example": {
                    "player_id": "v8lponvj",
                    "game_id": "n2680o1p",
                    "title": "Going for Any% WR",
                    "offline_ct": 0,
                    "stream_time": "2025-08-15T08:30:00Z",
                },
            }
        },
    },
}

STREAMS_PUT = {
    "responses": {
        200: {
            "description": "Stream updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "player": {"id": "v8lponvj", "name": "ThePackle"},
                        "game": {"id": "n2680o1p", "name": "Tony Hawk's Pro Skater 4"},
                        "title": "100% Speedrun Practice",
                        "offline_ct": 1,
                        "stream_time": "2025-08-15T08:30:00Z",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or game does not exist."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Stream does not exist for this player."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "player_id",
            "in": "path",
            "required": True,
            "example": "v8lponvj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Player ID to update stream for",
        },
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "UPDATED GAME ID",
                        },
                        "title": {
                            "type": "string",
                            "example": "100% Speedrun Practice",
                            "description": "UPDATED STREAM TITLE",
                        },
                        "offline_ct": {
                            "type": "integer",
                            "example": 1,
                            "description": "UPDATED OFFLINE COUNTER",
                        },
                        "stream_time": {
                            "type": "string",
                            "format": "date-time",
                            "example": "2025-08-15T08:30:00Z",
                            "description": "UPDATED STREAM START TIME",
                        },
                    },
                },
                "example": {
                    "title": "100% Speedrun Practice",
                    "offline_ct": 1,
                },
            }
        },
    },
}

STREAMS_DELETE = {
    "responses": {
        200: {
            "description": "Stream deleted successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Stream for player 'ThePackle' deleted successfully"
                    }
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Stream does not exist for this player."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "player_id",
            "in": "path",
            "required": True,
            "example": "v8lponvj",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Player ID to delete stream for",
        },
    ],
}
# END OPENAPI DOCUMENTATION #


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

    **Query Parameters:**
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
    auth=read_only_auth,
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
    """Get currently live streamers with filtering."""
    try:
        # Gets streaming data for testing purposes; TODO: DELETE BEFORE PROD.
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
    """,
    auth=api_moderator_check,
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

        response_data = {
            "player": {
                "id": player.id,
                "name": player.nickname if player.nickname else player.name,
            },
            "game": (
                {
                    "id": game.id,
                    "name": game.name,
                }
                if game
                else None
            ),
            "title": stream.title,
            "offline_ct": stream.offline_ct,
            "stream_time": stream.stream_time,
        }

        return StreamSchema(**response_data)

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
    """,
    auth=api_moderator_check,
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

        response_data = {
            "player": {
                "id": player.id,
                "name": player.nickname if player.nickname else player.name,
            },
            "game": (
                {
                    "id": stream.game.id,
                    "name": stream.game.name,
                }
                if stream.game
                else None
            ),
            "title": stream.title,
            "offline_ct": stream.offline_ct,
            "stream_time": stream.stream_time,
        }

        return StreamSchema(**response_data)

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
    """,
    auth=api_admin_check,
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
