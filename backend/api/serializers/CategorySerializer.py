from typing import Any, Union

from django.db.models import Q
from rest_framework import serializers
from srl.models import Categories, Games, Runs, Variables, VariableValues


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for category metadata.

    This serializer is used to return structured information about a specific category, including
    optional metadata from other models.

    SerializerMethodField:
        - game (dict): Contains information about the associated category's game.
        - variables (dict): Contains information about the associated category's variables.
        - values (dict): Contains information about the associated variable's values.
            - Note: This field assumes you will also want the variable information.
    """

    game = serializers.SerializerMethodField()
    variables = serializers.SerializerMethodField()

    def get_game(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        from api.serializers.core import GameSerializer

        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id)).data
        else:
            return None

    def get_variables(
        self,
        obj: Variables,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes variable information, to include optional embeds."""
        from api.serializers.core import ValueSerializer, VariableSerializer

        if "values" in self.context.get("embed", []):
            variable_lookup = Variables.objects.filter(
                game=obj.game, hidden=False
            ).filter(Q(cat=obj.id) | Q(cat__isnull=True))

            if obj.type == "per-level":
                variable_lookup = variable_lookup.exclude(scope="full-game")
            else:
                variable_lookup = variable_lookup.exclude(scope__contains="level")

            variables = VariableSerializer(
                variable_lookup,
                many=True,
            ).data

            for var in variables:
                values = ValueSerializer(
                    VariableValues.objects.filter(var=var["id"]), many=True
                ).data

                for v in values:
                    v.pop("variable", None)

                var["values"] = values

            return variables
        elif "variables" in self.context.get("embed", []):
            return VariableSerializer(
                Variables.objects.filter(cat=obj.id), many=True
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

        if "variables" not in embed_fields:
            data.pop("variables", None)
        else:
            for variable in data["variables"]:
                variable.pop("cat", None)

        return data

    class Meta:
        model = Categories
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "url",
            "hidden",
            "game",
            "variables",
        ]
