from datetime import datetime
from typing import Any, Union

from django.db.models import Q
from rest_framework import serializers
from srl.models import (
    Awards,
    Categories,
    Games,
    Levels,
    NowStreaming,
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
        game (dict): Contains information about the associated speedrun's game.
        category (dict): Contains information about the associated speedrun's category.
        level (dict): Contains information about the associated speedrun's level.
        variables (dict) Contains information about the associated speedrun's variables.
        times (dict): Contains information about the associated speedrun's times.
        record (dict): Contains information about the world record of the speedrun's category.
        players (dict): Contains information about the associated speedrun's variables.
        status (dict): Contains information about the associated speedrun's status.
        videos (dict): Contains information about the associated speedrun's videos.
        meta (dict): Contains information about the associated speedrun's  metadata.
    """

    game = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    variables = serializers.SerializerMethodField()
    times = serializers.SerializerMethodField()
    record = serializers.SerializerMethodField()
    players = serializers.SerializerMethodField()
    system = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    meta = serializers.SerializerMethodField()

    def get_game(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        if any(item in self.context.get("embed", []) for item in ["games", "game"]):
            return GameSerializer(Games.objects.get(id=obj.game.id)).data
        else:
            return obj.game.id

    def get_category(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes category information, to include optional embeds."""
        if "category" in self.context.get("embed", []):
            return CategorySerializer(Categories.objects.get(id=obj.category.id)).data
        else:
            return obj.category.id

    def get_level(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes level information, to include optional embeds."""
        if "level" in self.context.get("embed", []):
            return LevelSerializer(Levels.objects.get(id=obj.level.id)).data
        elif obj.level:
            return obj.level.id
        else:
            return None

    def get_times(self, obj: Runs) -> dict[dict, str]:
        """Serializes time information."""
        return {
            "defaulttime": obj.game.defaulttime,
            "time": obj.time,
            "time_secs": obj.time_secs,
            "timenl": obj.timenl,
            "timenl_secs": obj.timenl_secs,
            "timeigt": obj.timeigt,
            "timeigt_secs": obj.timeigt_secs,
        }

    def get_record(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes the world record associated with the run's subcategory"""

        if "record" in self.context.get("embed", []):
            record = Runs.objects.filter(
                game=obj.game, subcategory=obj.subcategory, place=1
            ).first()

            get_record = RunSerializer(Runs.objects.get(id=record.id)).data
            return get_record
        else:
            return (
                Runs.objects.only("id")
                .filter(game=obj.game, subcategory=obj.subcategory, place=1)
                .first()
                .id
            )

    def get_players(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes player information, to include optional embeds."""
        if "players" in self.context.get("embed", []):
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

    def get_system(self, obj: Runs) -> dict[dict, str]:
        """Serializes platform information, to include optional embeds."""
        if "platform" in self.context.get("embed", []):
            plat = PlatformSerializer(Platforms.objects.get(id=obj.platform.id)).data
        else:
            plat = obj.platform.id

        return {
            "platform": plat,
            "emulated": obj.emulated,
        }

    def get_status(self, obj: Runs) -> dict[dict, str]:
        """Serializes run status information."""
        return {
            "vid_status": obj.vid_status,
            "approver": obj.approver.id if obj.approver else None,
            "v_date": obj.v_date,
            "obsolete": obj.obsolete,
        }

    def get_videos(self, obj: Runs) -> dict[dict, str]:
        """Serializes video information."""
        return {
            "video": obj.video,
            "arch_video": obj.arch_video,
        }

    def get_variables(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes variable information, to include optional embeds."""

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

    def get_meta(self, obj: Runs) -> dict[dict, str]:
        """Serializes the run's metadata."""

        return {
            "points": obj.points,
            "url": obj.url,
        }

    def to_representation(self, instance) -> dict[dict, Any]:
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


class PlatformSerializer(serializers.ModelSerializer):
    """Serializer for platform metadata.

    This serializer is used to return structured information about a specific platform, including
    optional metadata from the `Games` model.

    SerializerMethodField:
        games (dict): Contains information about games that belong to that platform.
    """

    games = serializers.SerializerMethodField()

    def get_games(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        if "games" in self.context.get("embed", []):
            return GameSerializer(obj.game).data if obj.game else None
        else:
            return None

    def to_representation(self, instance) -> dict[str, Any]:
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


class PlayerSerializer(serializers.ModelSerializer):
    """Serializer for player metadata.

    This serializer is used to return structured information about a specific player.

    SerializerMethodField:
        stats (dict): Contains information about the associated player's stats.
        country (dict): Contains information about the associated player's country.
        awards (dict): Contains information about the associated player's awards.
    """

    stats = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    awards = serializers.SerializerMethodField()

    def get_stats(self, obj: Runs) -> dict[dict, str]:
        """Serializes basic stats for the player, including rankings and points."""
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

    def get_country(self, obj: Players) -> str:
        """Serializes country information."""
        if obj.countrycode:
            return obj.countrycode.name
        else:
            return None

    def get_awards(self, obj: Players) -> Union[str, int, dict[str, Any]]:
        """Serializes award information."""
        if obj.awards:
            return AwardSerializer(obj.awards, many=True).data
        else:
            return None

    def to_representation(self, instance) -> dict[str, Any]:
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


class PlayerStreamSerializer(serializers.ModelSerializer):
    """Serializer for player's stream information.

    This serializer is a minimalistic view of `PlayerSerializer` that only displays the player's
    streaming information (e.g. Twitch, YouTube, ex_stream).

    SerializerMethodField:
        stats (dict): Contains information about the associated player's stats.
        country (dict): Contains information about the associated player's country.
        awards (dict): Contains information about the associated player's awards.
    """

    twitch = serializers.SerializerMethodField()

    def get_twitch(self, obj: Players) -> str:
        """Serializes Twitch.tv metadata for players."""
        if obj.twitch:
            return obj.twitch.replace("https://www.twitch.tv/", "")
        else:
            obj.twitch

    def to_representation(self, instance) -> dict[str, Any]:
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


class GameSerializer(serializers.ModelSerializer):
    """Serializer for game metadata.

    This serializer is used to return structured information about a specific game, including
    optional metadata from other models.

    SerializerMethodField:
        categories (dict): Contains information about the associated game's categories.
        levels (dict): Contains information about the associated game's levels.
        platforms (dict): Contains information about the associated game's variables.
    """

    categories = serializers.SerializerMethodField()
    levels = serializers.SerializerMethodField()
    platforms = serializers.SerializerMethodField()

    def get_categories(self, obj: Games) -> Union[str, int, dict[str, Any]]:
        """Serializes category information, to include optional embeds."""
        if "categories" in self.context.get("embed", []):
            return CategorySerializer(
                Categories.objects.filter(game=obj), many=True
            ).data
        else:
            return None

    def get_levels(self, obj: Games) -> Union[str, int, dict[str, Any]]:
        """Serializes level information, to include optional embeds."""
        if "levels" in self.context.get("embed", []):
            return LevelSerializer(Levels.objects.filter(game=obj), many=True).data
        else:
            return None

    def get_platforms(self, obj: Games) -> Union[str, int, dict[str, Any]]:
        """Serializes platform information, to include optional embeds."""
        if "platforms" in self.context.get("embed", []):
            return PlatformSerializer(obj.platforms, many=True).data
        else:
            return None

    def to_representation(self, instance) -> dict[str, Any]:
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


class LevelSerializer(serializers.ModelSerializer):
    """Serializer for level metadata.

    This serializer is used to return structured information about a specific level, including
    optional metadata from other models.

    SerializerMethodField:
        game (dict): Contains information about the associated level's game.
    """

    game = serializers.SerializerMethodField()

    def get_game(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.get(id=obj.game.id)).data
        else:
            return None

    def to_representation(self, instance) -> dict[str, Any]:
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


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for category metadata.

    This serializer is used to return structured information about a specific category, including
    optional metadata from other models.

    SerializerMethodField:
        game (dict): Contains information about the associated category's game.
        variables (dict): Contains information about the associated category's variables.
    """

    game = serializers.SerializerMethodField()
    variables = serializers.SerializerMethodField()

    def get_game(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id)).data
        else:
            return None

    def get_variables(self, obj: Variables) -> Union[str, int, dict[str, Any]]:
        """Serializes variable information, to include optional embeds."""
        if "variables" in self.context.get("embed", []):
            return VariableSerializer(
                Variables.objects.filter(cat=obj.id), many=True
            ).data
        else:
            return None

    def to_representation(self, instance) -> dict[str, Any]:
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
        fields = ["id", "name", "type", "url", "hidden", "game", "variables"]


class VariableSerializer(serializers.ModelSerializer):
    """Serializer for variable metadata.

    This serializer is used to return structured information about a specific variable, including
    optional metadata from other models.

    SerializerMethodField:
        game (dict): Contains information about the associated game.
        values (dict): Contains information about the associated category.
    """

    game = serializers.SerializerMethodField()
    values = serializers.SerializerMethodField()

    def get_game(self, obj: Runs) -> Union[str, int, dict[str, Any]]:
        """Serializes game information, to include optional embeds."""
        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id), many=True).data
        else:
            return None

    def get_values(self, obj: Variables) -> Union[str, int, dict[str, Any]]:
        """Serializes value information, to include optional embeds."""
        if "values" in self.context.get("embed", []):
            return ValueSerializer(
                VariableValues.objects.filter(var=obj.id), many=True
            ).data
        else:
            return None

    def to_representation(self, instance) -> dict[str, Any]:
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


class ValueSerializer(serializers.ModelSerializer):
    """Serializer for value metadata.

    This serializer is used to return structured information about a specific value, including
    optional metadata from other models.

    SerializerMethodField:
        variable (dict): Contains information about the associated value's variable.
    """

    variable = serializers.SerializerMethodField()

    def get_variable(self, obj: VariableValues) -> Union[str, int, dict[str, Any]]:
        """Serializes variable information, to include optional embeds."""
        if "variable" in self.context.get("embed", []):
            return VariableSerializer(Variables.objects.get(id=obj.var.id)).data
        else:
            return obj.var.id

    def to_representation(self, instance) -> dict[str, Any]:
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


class AwardSerializer(serializers.ModelSerializer):
    """Serializer for awards metadata."""

    class Meta:
        model = Awards
        fields = ["name"]


class StreamSerializer(serializers.ModelSerializer):
    """Serializer for stream metadata.

    This serializer is used to return structured information about a specific stream, including
    optional metadata from other models.

    SerializerMethodField:
        streamer (dict): Contains information about the associated stream's streamer.
        game (dict): Contains information about the associated stream's game.
    """

    streamer = serializers.SerializerMethodField()
    game = serializers.SerializerMethodField()

    def get_streamer(self, obj: NowStreaming) -> dict[dict, str]:
        """Serializes streamer information."""
        return {
            "player": obj.streamer.name,
            "twitch": obj.streamer.twitch,
            "youtube": obj.streamer.youtube,
        }

    def get_game(self, obj: NowStreaming) -> dict[dict, str]:
        """Serializes game information."""
        return {
            "id": obj.game.id,
            "name": obj.game.name,
            "twitch": obj.game.twitch,
        }

    class Meta:
        model = NowStreaming
        fields = ["streamer", "game", "title", "offline_ct", "stream_time"]


class StreamSerializerPost(serializers.ModelSerializer):
    """Serializer for POST'ing stream metadata..

    This serializer is used to POST structured information about a specific stream, including
    optional metadata from other models.

    SerializerMethodField:
        streamer (str): Contains information about the associated stream's streamer name.
        game (str): Contains information about the associated stream's game name.
        title (str):  Contains information about the associated stream's title.
        offline_ct (int):  Contains information about the associated stream's offline counter.
        stream_time (date):  Contains information about the associated stream's start stream time.
    """

    streamer = serializers.CharField()
    game = serializers.CharField()
    title = serializers.CharField()
    offline_ct = serializers.IntegerField()
    stream_time = serializers.CharField()

    def validate_streamer(self, streamer):
        """Validates if the streamer exists in the `Streamer` model."""
        try:
            return Players.objects.get(
                Q(id__iexact=streamer)
                | Q(name__iexact=streamer)
                | Q(twitch__icontains=streamer)
            )
        except Players.DoesNotExist:
            raise serializers.ValidationError("streamer name or ID does not exist.")

    def validate_game(self, gameid) -> Games:
        """Validates if the game exists in the `Games` model."""
        try:
            return Games.objects.only("id").get(
                Q(id__iexact=gameid) | Q(name__iexact=gameid) | Q(slug__iexact=gameid)
            )
        except Games.DoesNotExist:
            raise serializers.ValidationError(
                "game name, ID, or slug/abbreviation does not exist."
            )

    def validate_title(self, title) -> str:
        """Validates if the stream's title is above 0 and below 100."""
        if len(title) == 0 or len(title) > 100:
            raise serializers.ValidationError("title length is 0 or greater than 100.")

        return title

    def validate_offline_ct(self, count) -> str:
        """Validates if the offline counter is an integer and above 0."""
        if isinstance(count, str):
            raise serializers.ValidationError("offline_ct must be an integer.")

        if count < 0:
            raise serializers.ValidationError("offline_ct must be a positive integer.")
        elif count > 0:
            return count
        else:
            raise serializers.ValidationError("offline_ct must be an integer.")

    def validate_stream_time(self, streamtime) -> str:
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


class PlayerSerializerPost(serializers.ModelSerializer):
    """Serializer for POST'ing player metadata..

    This serializer is used to POST structured information about a specific player.

    SerializerMethodField:
        ex_stream (bool): Contains information on how to set `ex_stream` for the player.
    """

    ex_stream = serializers.BooleanField()
    nickname = serializers.CharField()

    def validate_ex_stream(self, ex_stream: Union[bool, str]) -> bool:
        """Validates if the ex_stream field is properly setup."""
        if isinstance(ex_stream, bool):
            return ex_stream
        elif ex_stream == "True":
            return True
        elif ex_stream == "False":
            return False
        else:
            raise serializers.ValidationError("ex_stream is a boolean True or False.")

    def validate_nickname(self, nickname: str) -> str:
        """Validates if the nickname field is properly setup."""
        if len(nickname) > 30:
            raise serializers.ValidationError(
                "nickname field must be 30 characters or less."
            )

    class Meta:
        model = Players
        fields = ["ex_stream"]
