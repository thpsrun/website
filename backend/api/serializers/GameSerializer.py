from typing import Any, Union

from rest_framework import serializers
from srl.models import Categories, Games, Levels


class GameSerializer(serializers.ModelSerializer):
    """Serializer for game metadata.

    This serializer is used to return structured information about a specific game, including
    optional metadata from other models.

    SerializerMethodField:
        - categories (dict): Contains information about the associated game's categories.
        - levels (dict): Contains information about the associated game's levels.
        - platforms (dict): Contains information about the associated game's variables.
    """

    categories = serializers.SerializerMethodField()
    levels = serializers.SerializerMethodField()
    platforms = serializers.SerializerMethodField()

    def get_categories(
        self,
        obj: Games,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes category information, to include optional embeds."""
        from api.serializers.core import CategorySerializer

        if "categories" in self.context.get("embed", []):
            return CategorySerializer(
                Categories.objects.filter(game=obj), many=True
            ).data
        else:
            return None

    def get_levels(
        self,
        obj: Games,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes level information, to include optional embeds."""
        from api.serializers.core import LevelSerializer

        if "levels" in self.context.get("embed", []):
            return LevelSerializer(Levels.objects.filter(game=obj), many=True).data
        else:
            return None

    def get_platforms(
        self,
        obj: Games,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes platform information, to include optional embeds."""
        from api.serializers.core import PlatformSerializer

        if "platforms" in self.context.get("embed", []):
            return PlatformSerializer(obj.platforms, many=True).data
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

        if "categories" not in embed_fields:
            data.pop("categories", None)

        if "levels" not in embed_fields:
            data.pop("levels", None)

        if "platforms" not in embed_fields:
            data.pop("platforms", None)

        return data

    class Meta:
        model = Games
        fields = [
            "id",
            "name",
            "slug",
            "release",
            "boxart",
            "twitch",
            "defaulttime",
            "idefaulttime",
            "pointsmax",
            "ipointsmax",
            "categories",
            "levels",
            "platforms",
        ]
