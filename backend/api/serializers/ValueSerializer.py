from typing import Any, Union

from rest_framework import serializers
from srl.models import Variables, VariableValues


class ValueSerializer(serializers.ModelSerializer):
    """Serializer for value metadata.

    This serializer is used to return structured information about a specific value, including
    optional metadata from other models.

    SerializerMethodField:
        - variable (dict): Contains information about the associated value's variable.
    """

    variable = serializers.SerializerMethodField()

    def get_variable(
        self,
        obj: VariableValues,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes variable information, to include optional embeds."""
        from api.serializers.core import VariableSerializer

        if "variable" in self.context.get("embed", []):
            return VariableSerializer(Variables.objects.get(id=obj.var.id)).data
        else:
            return obj.var.id

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

        return data

    class Meta:
        model = VariableValues
        fields = ["value", "name", "hidden", "variable"]
