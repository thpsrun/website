from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from django.db.models import Q
from django.http import HttpRequest
from ninja import Path, Query, Router
from srl.models import Games, Players, Runs

from api.auth.api_key import read_only_auth
from api.schemas.base import ErrorResponse
from api.schemas.streams import LiveStatsSchema, StreamSchema

streams_router = Router(tags=["Streams"])


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


@streams_router.get(
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
)
def get_live_streams(
    request: HttpRequest,
    game_id: Optional[str] = Query(None, description="Filter by game"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    min_viewers: Optional[int] = Query(None, description="Minimum viewers", ge=0),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
) -> Union[List[StreamSchema], ErrorResponse]:
    """Get currently live streamers with filtering."""
    try:
        # Get streaming data (mock for demo - replace with real API calls)
        streams_data = get_mock_streaming_data()

        # Apply filters
        filtered_streams = []
        for stream in streams_data:
            # Game filter
            if game_id and stream["game"]:
                if stream["game"]["id"] != game_id:
                    continue

            # Platform filter
            if platform and stream["platform"] != platform:
                continue

            # Minimum viewers filter
            if min_viewers and (
                not stream["viewers"] or stream["viewers"] < min_viewers
            ):
                continue

            filtered_streams.append(stream)

        # Apply limit
        limited_streams = filtered_streams[:limit]

        # Convert to schemas
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


@streams_router.get(
    "/stats",
    response=Union[LiveStatsSchema, ErrorResponse],
    summary="Get Live Streaming Statistics",
    description="""
    Get real-time statistics about speedrunning streaming activity.

    **Returns:**
    - Total number of active streamers
    - Total viewers across all streams
    - Most popular games being streamed
    - Recent speedrunning activity

    **Use Case:**
    Perfect for dashboard widgets, activity feeds, and community statistics.
    """,
    auth=read_only_auth,
)
def get_streaming_stats(
    request: HttpRequest,
) -> Union[LiveStatsSchema, ErrorResponse]:
    """Get live streaming statistics."""
    try:
        # Get current streaming data
        streams_data = get_mock_streaming_data()

        # Calculate statistics
        total_streamers = len(streams_data)
        total_viewers = sum(stream.get("viewers", 0) for stream in streams_data)

        # Get top games by stream count
        game_counts = {}
        for stream in streams_data:
            if stream.get("game"):
                game_name = stream["game"]["name"]
                game_counts[game_name] = game_counts.get(game_name, 0) + 1

        top_games = [
            {"game": game, "streamers": count}
            for game, count in sorted(
                game_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        # Get recent activity from database
        recent_runs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .select_related("game", "player", "category")
            .filter(v_date__gte=datetime.now() - timedelta(hours=24))
            .order_by("-v_date")[:10]
        )

        recent_activity = []
        for run in recent_runs:
            recent_activity.append(
                {
                    "type": "run",
                    "player": run.player.name if run.player else "Unknown",
                    "game": run.game.name if run.game else "Unknown",
                    "category": run.category.name if run.category else "Unknown",
                    "time": run.time,
                    "place": run.place,
                    "date": run.v_date.isoformat() if run.v_date else None,
                }
            )

        stats = LiveStatsSchema(
            total_streamers=total_streamers,
            total_viewers=total_viewers,
            top_games=top_games,
            recent_activity=recent_activity,
            last_updated=datetime.now(),
        )

        return stats

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve streaming statistics",
            details={"exception": str(e)},
            code=500,
        )


@streams_router.get(
    "/player/{player_id}",
    response=Union[Dict[str, Any], ErrorResponse],
    summary="Get Player Streaming Info",
    description="""
    Get streaming information for a specific player.

    **Returns:**
    - Whether player is currently streaming
    - Stream details if live
    - Player's streaming history/statistics
    - Social media links for streaming platforms
    """,
    auth=read_only_auth,
)
def get_player_streaming_info(
    request: HttpRequest,
    player_id: str = Path(..., description="Player ID"),
) -> Union[Dict[str, Any], ErrorResponse]:
    """Get streaming info for a specific player."""
    try:
        # Validate player exists
        player = Players.objects.filter(id=player_id).first()
        if not player:
            return ErrorResponse(error="Player not found", code=404)

        # Check if player is currently streaming (mock data)
        streams_data = get_mock_streaming_data()
        current_stream = None

        for stream in streams_data:
            if stream["player"]["id"] == player_id:
                current_stream = stream
                break

        # Get player's streaming-related info
        streaming_info = {
            "player": {
                "id": player.id,
                "name": player.nickname if player.nickname else player.name,
                "twitch": player.twitch,
                "youtube": player.youtube,
            },
            "is_live": current_stream is not None,
            "current_stream": current_stream,
            "stream_exception": player.ex_stream,
            "streaming_platforms": [],
        }

        # Add streaming platforms if available
        if player.twitch:
            streaming_info["streaming_platforms"].append(
                {"platform": "twitch", "url": player.twitch, "primary": True}
            )

        if player.youtube:
            streaming_info["streaming_platforms"].append(
                {"platform": "youtube", "url": player.youtube, "primary": False}
            )

        return streaming_info

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve player streaming info",
            details={"exception": str(e)},
            code=500,
        )


@streams_router.get(
    "/game/{game_id}",
    response=Union[List[StreamSchema], ErrorResponse],
    summary="Get Streamers by Game",
    description="""
    Get all streamers currently playing a specific game.

    **Query Parameters:**
    - `min_viewers`: Minimum viewer count filter
    - `limit`: Maximum results (default 10, max 25)

    **Use Case:**
    Perfect for game-specific pages to show who's currently streaming that game.
    """,
    auth=read_only_auth,
)
def get_streamers_by_game(
    request: HttpRequest,
    game_id: str = Path(..., description="Game ID or slug"),
    min_viewers: Optional[int] = Query(None, description="Minimum viewers", ge=0),
    limit: int = Query(10, ge=1, le=25),
) -> Union[List[StreamSchema], ErrorResponse]:
    """Get streamers playing a specific game."""
    try:
        # Validate game exists
        game = Games.objects.filter(Q(id=game_id) | Q(slug=game_id)).first()
        if not game:
            return ErrorResponse(error="Game not found", code=404)

        # Get streaming data filtered by game
        streams_data = get_mock_streaming_data()
        game_streams = []

        for stream in streams_data:
            if stream.get("game") and (
                stream["game"]["id"] == game_id or stream["game"]["id"] == game.id
            ):
                # Apply viewer filter
                if min_viewers and (
                    not stream["viewers"] or stream["viewers"] < min_viewers
                ):
                    continue

                game_streams.append(stream)

        # Apply limit and sort by viewers
        game_streams.sort(key=lambda x: x.get("viewers", 0), reverse=True)
        limited_streams = game_streams[:limit]

        # Convert to schemas
        stream_schemas = [StreamSchema(**stream) for stream in limited_streams]

        return stream_schemas

    except Exception as e:
        return ErrorResponse(
            error="Failed to retrieve game streams",
            details={"exception": str(e)},
            code=500,
        )
