from datetime import datetime

from django.db.models import Q
from rest_framework import serializers
from srl.models import Games, NowStreaming, Players


class StreamSerializerPost(serializers.ModelSerializer):
    """Serializer for POST'ing stream metadata..

    This serializer is used to POST structured information about a specific stream, including
    optional metadata from other models.

    SerializerMethodField:
        - streamer (str): Contains information about the associated stream's streamer name.
        - game (str): Contains information about the associated stream's game name.
        - title (str):  Contains information about the associated stream's title.
        - offline_ct (int):  Contains information about the associated stream's offline counter.
        - stream_time (date):  Contains information about the associated stream's start stream time.
    """

    streamer = serializers.CharField()
    game = serializers.CharField()
    title = serializers.CharField()
    offline_ct = serializers.IntegerField()
    stream_time = serializers.CharField()

    def validate_streamer(
        self,
        streamer: str,
    ) -> Players:
        """Validates if the streamer exists in the `Streamer` model."""
        try:
            return Players.objects.get(
                Q(id__iexact=streamer)
                | Q(name__iexact=streamer)
                | Q(twitch__icontains=streamer)
            )
        except Players.DoesNotExist:
            raise serializers.ValidationError("streamer name or ID does not exist.")

    def validate_game(
        self,
        gameid,
    ) -> Games:
        """Validates if the game exists in the `Games` model."""
        try:
            return Games.objects.only("id").get(
                Q(id__iexact=gameid) | Q(name__iexact=gameid) | Q(slug__iexact=gameid)
            )
        except Games.DoesNotExist:
            raise serializers.ValidationError(
                "game name, ID, or slug/abbreviation does not exist."
            )

    def validate_title(
        self,
        title: str,
    ) -> str:
        """Validates if the stream's title is above 0 and below 100."""
        if len(title) == 0 or len(title) > 100:
            raise serializers.ValidationError("title length is 0 or greater than 100.")

        return title

    def validate_offline_ct(
        self,
        count: int,
    ) -> str:
        """Validates if the offline counter is an integer and above 0."""
        if isinstance(count, str):
            raise serializers.ValidationError("offline_ct must be an integer.")

        if count < 0:
            raise serializers.ValidationError("offline_ct must be a positive integer.")
        elif count > 0:
            return count
        else:
            raise serializers.ValidationError("offline_ct must be an integer.")

    def validate_stream_time(
        self,
        streamtime: str,
    ) -> str:
        """Validates if the stream start time is a valid date/time field."""
        try:
            correct_time = datetime.fromisoformat(
                streamtime.replace("Z", "+00:00")
            ).replace(tzinfo=None)

            if correct_time > datetime.now():
                raise serializers.ValidationError(
                    "stream_time cannot be in the future."
                )
            else:
                return correct_time
        except Exception:
            raise serializers.ValidationError(
                "Invalid date time format --- Example: '2024-12-31T06:23:51.188Z'"
            )

    class Meta:
        model = NowStreaming
        fields = ["streamer", "game", "title", "offline_ct", "stream_time"]
