from typing import Any, Union

from django.db.models import Q
from rest_framework import serializers
from srl.models import Players, Runs


class PlayerSerializer(serializers.ModelSerializer):
    """Serializer for player metadata.

    This serializer is used to return structured information about a specific player.

    SerializerMethodField:
        - stats (dict): Contains information about the associated player's stats.
        - country (dict): Contains information about the associated player's country.
        - awards (dict): Contains information about the associated player's awards.
    """

    stats = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    awards = serializers.SerializerMethodField()

    def get_stats(
        self,
        obj: Runs,
    ) -> dict[dict, str]:
        """Serializes basic stats for the player, including rankings and points."""
        if "stats" in self.context.get("embed", []):
            main_runs = (
                Runs.objects.only("points", "obsolete")
                .filter(runtype="main")
                .filter(Q(player=obj.id) | Q(player2=obj.id))
            )

            il_runs = Runs.objects.only("points", "obsolete").filter(
                runtype="il", player=obj.id
            )

            main_points = sum(run.points for run in main_runs.filter(obsolete=False))
            il_points = sum(run.points for run in il_runs.filter(obsolete=False))
            total_pts = main_points + il_points

            total_runs = len(main_runs) + len(il_runs)

            return {
                "total_pts": total_pts,
                "main_pts": main_points,
                "il_pts": il_points,
                "total_runs": total_runs,
            }
        else:
            return None

    def get_country(
        self,
        obj: Players,
    ) -> str:
        """Serializes country information."""
        if obj.countrycode:
            return obj.countrycode.id
        else:
            return None

    def get_awards(
        self,
        obj: Players,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes award information."""
        from api.serializers.core import AwardSerializer

        if obj.awards:
            return AwardSerializer(obj.awards, many=True).data
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
        return super().to_representation(instance)

    class Meta:
        model = Players
        fields = [
            "id",
            "name",
            "nickname",
            "url",
            "pfp",
            "country",
            "pronouns",
            "twitch",
            "youtube",
            "twitter",
            "ex_stream",
            "awards",
            "stats",
        ]
