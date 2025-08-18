from rest_framework import serializers
from srl.models import NowStreaming


class StreamSerializer(serializers.ModelSerializer):
    """Serializer for stream metadata.

    This serializer is used to return structured information about a specific stream, including
    optional metadata from other models.

    SerializerMethodField:
        - streamer (dict): Contains information about the associated stream's streamer.
        - game (dict): Contains information about the associated stream's game.
    """

    streamer = serializers.SerializerMethodField()
    game = serializers.SerializerMethodField()

    def get_streamer(
        self,
        obj: NowStreaming,
    ) -> dict[dict, str]:
        """Serializes streamer information."""
        return {
            "player": obj.streamer.name,
            "twitch": obj.streamer.twitch,
            "youtube": obj.streamer.youtube,
        }

    def get_game(
        self,
        obj: NowStreaming,
    ) -> dict[dict, str]:
        """Serializes game information."""
        return {
            "id": obj.game.id,
            "name": obj.game.name,
            "twitch": obj.game.twitch,
        }

    class Meta:
        model = NowStreaming
        fields = ["streamer", "game", "title", "offline_ct", "stream_time"]
