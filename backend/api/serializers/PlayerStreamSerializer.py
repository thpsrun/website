from typing import Any

from rest_framework import serializers
from srl.models import Players


class PlayerStreamSerializer(serializers.ModelSerializer):
    """Serializer for player's stream information.

    This serializer is a minimalistic view of `PlayerSerializer` that only displays the player's
    streaming information (e.g. Twitch, YouTube, ex_stream).

    SerializerMethodField:
        - stats (dict): Contains information about the associated player's stats.
        - country (dict): Contains information about the associated player's country.
        - awards (dict): Contains information about the associated player's awards.
    """

    twitch = serializers.SerializerMethodField()

    def get_twitch(
        self,
        obj: Players,
    ) -> str:
        """Serializes Twitch.tv metadata for players."""
        if obj.twitch:
            return obj.twitch.replace("https://www.twitch.tv/", "")
        else:
            obj.twitch

    def to_representation(
        self,
        instance,
    ) -> dict[str, Any]:
        """Customizes the serialized output of the object.

        This method overrides default fields normally returned by the JSON object. All of these
        fields are customized or nested into other fields, so the default response isn't needed.

        Args:
            instance (Model): The instanced information being serialized.

        Returns:
            dict: The final serialized representation in JSON form.

        """
        return super().to_representation(instance)

    class Meta:
        model = Players
        fields = ["id", "name", "twitch", "youtube", "ex_stream"]
