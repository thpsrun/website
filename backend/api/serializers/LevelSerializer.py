from typing import Any, Union

from rest_framework import serializers
from srl.models import Games, Levels, Runs


class LevelSerializer(serializers.ModelSerializer):
    """Serializer for level metadata.

    This serializer is used to return structured information about a specific level, including
    optional metadata from other models.

    SerializerMethodField:
        - game (dict): Contains information about the associated level's game.
    """

    game = serializers.SerializerMethodField()

    def get_game(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        from api.serializers.core import GameSerializer

        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.get(id=obj.game.id)).data
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

        if "game" not in embed_fields:
            data.pop("game", None)

        return data

    class Meta:
        model = Levels
        fields = ["id", "name", "url", "game"]
