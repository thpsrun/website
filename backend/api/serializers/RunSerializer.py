from typing import Any, Union

from rest_framework import serializers
from srl.models import (
    Categories,
    Games,
    Levels,
    Platforms,
    Players,
    Runs,
    RunVariableValues,
    Variables,
    VariableValues,
)


class RunSerializer(serializers.ModelSerializer):
    """Serializer for run metadata.

    This serializer is used to return structured information about a specific speedrun, including
    optional metadata from other models.

    SerializerMethodField:
        - game (dict): Contains information about the associated speedrun's game.
        - category (dict): Contains information about the associated speedrun's category.
        - level (dict): Contains information about the associated speedrun's level.
        - variables (dict) Contains information about the associated speedrun's variables.
        - times (dict): Contains information about the associated speedrun's times.
        - record (dict): Contains information about the world record of the speedrun's category.
        - players (dict): Contains information about the associated speedrun's variables.
        - status (dict): Contains information about the associated speedrun's status.
        - videos (dict): Contains information about the associated speedrun's videos.
        - meta (dict): Contains information about the associated speedrun's  metadata.
    """

    game = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    variables = serializers.SerializerMethodField()
    times = serializers.SerializerMethodField()
    record = serializers.SerializerMethodField()
    lb_count = serializers.SerializerMethodField()
    players = serializers.SerializerMethodField()
    system = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    meta = serializers.SerializerMethodField()

    def get_game(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        from api.serializers.core import GameSerializer

        if any(item in self.context.get("embed", []) for item in ["games", "game"]):
            return GameSerializer(Games.objects.get(id=obj.game.id)).data
        else:
            return obj.game.id

    def get_category(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes category information, to include optional embeds."""
        from api.serializers.core import CategorySerializer

        if "category" in self.context.get("embed", []):
            return CategorySerializer(Categories.objects.get(id=obj.category.id)).data
        else:
            return obj.category.id

    def get_level(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes level information, to include optional embeds."""
        from api.serializers.core import LevelSerializer

        if "level" in self.context.get("embed", []):
            return LevelSerializer(Levels.objects.get(id=obj.level.id)).data
        elif obj.level:
            return obj.level.id
        else:
            return None

    def get_times(
        self,
        obj: Runs,
    ) -> dict[dict, str]:
        """Serializes time information."""
        return {
            "defaulttime": (
                obj.game.idefaulttime if obj.runtype == "il" else obj.game.defaulttime
            ),
            "time": obj.time,
            "time_secs": obj.time_secs,
            "timenl": obj.timenl,
            "timenl_secs": obj.timenl_secs,
            "timeigt": obj.timeigt,
            "timeigt_secs": obj.timeigt_secs,
        }

    def get_record(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes the world record associated with the run's subcategory."""
        record = (
            Runs.objects.only("id")
            .filter(
                game=obj.game,
                subcategory=obj.subcategory,
                place=1,
                obsolete=False,
            )
            .first()
        )
        if record:
            if "record" in self.context.get("embed", []):
                get_record = RunSerializer(Runs.objects.get(id=record.id)).data
                return get_record
            else:
                return record.id
        else:
            return None

    def get_lb_count(
        self,
        obj: Runs,
    ) -> int:
        """Serializes the number of players within a game and its subcategory."""
        player_count = (
            Runs.objects.only("id")
            .filter(
                game=obj.game,
                subcategory=obj.subcategory,
                obsolete=False,
            )
            .count()
        )

        return player_count

    def get_players(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes player information, to include optional embeds."""
        from api.serializers.core import PlayerSerializer

        if "players" in self.context.get("embed", []) and obj.player:
            player1 = PlayerSerializer(Players.objects.get(id=obj.player.id)).data

            if obj.player2:
                player2 = PlayerSerializer(Players.objects.get(id=obj.player2.id)).data
                return player1, player2
            else:
                return player1
        else:
            p1 = obj.player.id if obj.player else "Anonymous"

            if obj.player2 and "co-op" in obj.subcategory.lower():
                p2 = obj.player2.id
            elif "co-op" in obj.subcategory.lower():
                p2 = "Anonymous"
            else:
                return p1

            return p1, p2

    def get_system(
        self,
        obj: Runs,
    ) -> dict[dict, str]:
        """Serializes platform information, to include optional embeds."""
        from api.serializers.core import PlatformSerializer

        if "platform" in self.context.get("embed", []):
            plat = PlatformSerializer(Platforms.objects.get(id=obj.platform.id)).data
        else:
            plat = obj.platform.id

        return {
            "platform": plat,
            "emulated": obj.emulated,
        }

    def get_status(
        self,
        obj: Runs,
    ) -> dict[dict, str]:
        """Serializes run status information."""
        return {
            "vid_status": obj.vid_status,
            "approver": obj.approver.id if obj.approver else None,
            "v_date": obj.v_date,
            "obsolete": obj.obsolete,
        }

    def get_videos(
        self,
        obj: Runs,
    ) -> dict[dict, str]:
        """Serializes video information."""
        return {
            "video": obj.video,
            "arch_video": obj.arch_video,
        }

    def get_variables(
        self,
        obj: Runs,
    ) -> Union[str, int, dict[str, Any]]:
        """Serializes variable information, to include optional embeds."""
        from api.serializers.core import ValueSerializer, VariableSerializer

        variable_list = (
            RunVariableValues.objects.only("variable_id", "value_id")
            .filter(run=obj.id)
            .values("variable_id", "value_id")
        )

        output = {}

        if "variables" in self.context.get("embed", []):
            for variable in variable_list:
                var = VariableSerializer(
                    Variables.objects.only("id").get(id=variable["variable_id"])
                ).data

                val = ValueSerializer(
                    VariableValues.objects.only("value").get(value=variable["value_id"])
                ).data

                var_id = var["id"]
                var.pop("id", None)

                output.update(
                    {
                        var_id: {
                            **var,
                            "values": val,
                        }
                    }
                )
        else:
            if len(variable_list) > 0:
                for variable in variable_list:
                    output.update({variable["variable_id"]: variable["value_id"]})

        return output

    def get_meta(
        self,
        obj: Runs,
    ) -> dict[dict, str]:
        """Serializes the run's metadata."""

        return {
            "points": obj.points,
            "url": obj.url,
        }

    def to_representation(
        self,
        instance,
    ) -> dict[dict, Any]:
        """Customizes the serialized output of the object.

        This method overrides default fields normally returned by the JSON object. All of these
        fields are customized or nested into other fields, so the default response isn't needed.

        Args:
            instance (Model): The instanced information being serialized.

        Returns:
            dict: The final serialized representation in JSON form.

        """
        data = super().to_representation(instance)
        data.pop("player", None)
        data.pop("player2", None)
        data.pop("time_secs", None)
        data.pop("timenl", None)
        data.pop("timenl_secs", None)
        data.pop("timeigt", None)
        data.pop("timeigt_secs", None)
        data.pop("vid_status", None)
        data.pop("emulated", None)
        data.pop("approver", None)
        data.pop("v_date", None)
        data.pop("platform", None)
        data.pop("obsolete", None)
        data.pop("v_date", None)
        data.pop("video", None)
        data.pop("arch_video", None)
        data.pop("points", None)
        data.pop("url", None)

        if "record" in self.context.get("embed", []):
            if data.get("record"):
                data["record"].pop("record", None)

        return data

    class Meta:
        model = Runs
        fields = [
            "id",
            "runtype",
            "game",
            "platform",
            "category",
            "level",
            "subcategory",
            "place",
            "lb_count",
            "player",
            "player2",
            "players",
            "url",
            "video",
            "arch_video",
            "date",
            "v_date",
            "record",
            "times",
            "time_secs",
            "timenl",
            "timenl_secs",
            "timeigt",
            "timeigt_secs",
            "points",
            "emulated",
            "vid_status",
            "obsolete",
            "system",
            "status",
            "videos",
            "variables",
            "meta",
            "description",
        ]
