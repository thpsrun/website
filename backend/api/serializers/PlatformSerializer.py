from typing import Any, Union

from rest_framework import serializers
from srl.models import Platforms, Runs


class PlatformSerializer(serializers.ModelSerializer):
    """Serializer for platform metadata.

    This serializer is used to return structured information about a specific platform, including
    optional metadata from the `Games` model.

    SerializerMethodField:
        - games (dict): Contains information about games that belong to that platform.
    """

    games = serializers.SerializerMethodField()

    def get_games(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        from api.serializers.core import GameSerializer

        if "games" in self.context.get("embed", []):
            return GameSerializer(obj.game).data if obj.game else None
        else:
            return None

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
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed", [])

        if "games" not in embed_fields:
            data.pop("games", None)

        return data

    class Meta:
        model = Platforms
        fields = ["id", "name", "games"]
