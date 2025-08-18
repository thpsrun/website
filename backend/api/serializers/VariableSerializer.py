from typing import Any, Union

from rest_framework import serializers
from srl.models import Games, Runs, Variables, VariableValues


class VariableSerializer(serializers.ModelSerializer):
    """Serializer for variable metadata.

    This serializer is used to return structured information about a specific variable, including
    optional metadata from other models.

    SerializerMethodField:
        - game (dict): Contains information about the associated game.
        - values (dict): Contains information about the associated category.
    """

    game = serializers.SerializerMethodField()
    values = serializers.SerializerMethodField()

    def get_game(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        from api.serializers.core import GameSerializer

        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id), many=True).data
        else:
            return None

    def get_values(
        self,
        obj: Variables,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes value information, to include optional embeds."""
        from api.serializers.core import ValueSerializer

        if "values" in self.context.get("embed", []):
            return ValueSerializer(
                VariableValues.objects.filter(var=obj.id), many=True
            ).data
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

        if "values" not in embed_fields:
            data.pop("values", None)
        else:
            for value in data["values"]:
                value.pop("variable", None)

        return data

    class Meta:
        model = Variables
        fields = ["id", "name", "cat", "all_cats", "scope", "hidden", "game", "values"]
