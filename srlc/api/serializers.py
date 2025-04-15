from datetime import datetime

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


### Used in GET /runs/ endpoint.
class RunSerializer(serializers.ModelSerializer):
    game        = serializers.SerializerMethodField()
    category    = serializers.SerializerMethodField()
    level       = serializers.SerializerMethodField()
    variables   = serializers.SerializerMethodField()
    times       = serializers.SerializerMethodField()
    players     = serializers.SerializerMethodField()
    system      = serializers.SerializerMethodField()
    status      = serializers.SerializerMethodField()
    videos      = serializers.SerializerMethodField()
    meta        = serializers.SerializerMethodField()

    def get_game(self, obj):
        if any(item in self.context.get("embed", []) for item in ["games", "game"]):
            return GameSerializer(Games.objects.get(id=obj.game.id)).data
        else:
            return obj.game.id
        
    def get_category(self, obj):
        if "category" in self.context.get("embed", []):
            return CategorySerializer(Categories.objects.get(id=obj.category.id)).data
        else:
            return obj.category.id
        
    def get_level(self, obj):
        if "level" in self.context.get("embed", []):
            return LevelSerializer(Levels.objects.get(id=obj.level.id)).data
        elif obj.level:
            return obj.level.id
        else:
            return None
        
    def get_times(self, obj):
        return ({
            "defaulttime"   : obj.game.defaulttime,
            "time"          : obj.time,
            "time_secs"     : obj.time_secs,
            "timenl"        : obj.timenl,
            "timenl_secs"   : obj.timenl_secs,
            "timeigt"       : obj.timeigt,
            "timeigt_secs"  : obj.timeigt_secs,
        })
        
    def get_players(self, obj):
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
        
    def get_system(self, obj):
        if "platform" in self.context.get("embed", []):
            plat = PlatformSerializer(Platforms.objects.get(id=obj.platform.id)).data
        else:
            plat = obj.platform.id

        return ({
            "platform"      : plat,
            "emulated"      : obj.emulated,
        })
        
    def get_status(self, obj):
        return ({
            "vid_status"    : obj.vid_status,
            "approver"      : obj.approver.id,
            "v_date"        : obj.v_date,
            "obsolete"      : obj.obsolete,
        })
    
    def get_videos(self, obj):
        return ({
            "video"         : obj.video,
            "arch_video"    : obj.arch_video,
        })
    
    def get_variables(self, obj):
        variable_list = RunVariableValues.objects.only("variable_id", "value_id").filter(run=obj.id).values("variable_id", "value_id")
        output = {}

        if "variables" in self.context.get("embed", []):
            for variable in variable_list:
                var = VariableSerializer(Variables.objects.only("id").get(id=variable["variable_id"])).data
                val = ValueSerializer(VariableValues.objects.only("value").get(value=variable["value_id"])).data
                
                var_id = var["id"]
                var.pop("id", None)

                output.update({
                    var_id : {
                        **var,
                        "values": val,
                    }
                })
        else:
            if len(variable_list) > 0:
                for variable in variable_list:
                    output.update({
                        variable["variable_id"] : variable["value_id"]
                    })
                
        return output
    
    def get_meta(self, obj):
        return ({
            "points"    : obj.points,
            "url"       : obj.url,
        })
    
    def to_representation(self, instance):
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

        return data

    class Meta:
        model  = Runs
        fields = ["id", "runtype", "game", "platform", "category", "level",
                "subcategory", "place", "player", "player2", "players", 
                "url", "video", "arch_video", "date", "v_date", "times", "time_secs",
                "timenl", "timenl_secs", "timeigt", "timeigt_secs", "points", "emulated", 
                "vid_status", "obsolete", "system", "status", "videos", "variables", "meta"
        ]

### Used with the /platform/ endpoint.
class PlatformSerializer(serializers.ModelSerializer):
    games = serializers.SerializerMethodField()

    def get_games(self, obj):
        if "games" in self.context.get("embed", []):
            return GameSerializer(obj.game).data if obj.game else None
        else:
            return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed", [])

        if "games" not in embed_fields:
            data.pop("games", None)

        return data
    
    class Meta:
        model  = Platforms
        fields = ["id", "name", "games"]

### Used with the /players/ endpoint
class PlayerSerializer(serializers.ModelSerializer):
    stats   = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    awards  = serializers.SerializerMethodField()

    def get_stats(self, obj):
        main_runs   = Runs.objects.filter(runtype="main", points__gt=0).filter(Q(player=obj.id) | Q(player2=obj.id))
        il_runs     = Runs.objects.filter(runtype="il", player=obj.id, points__gt=0)

        main_points = sum(run.points for run in main_runs.filter(obsolete=False))
        il_points   = sum(run.points for run in il_runs.filter(obsolete=False))
        total_pts   = main_points + il_points

        total_runs  = len(main_runs) + len(il_runs)

        return {
            "total_pts" : total_pts,
            "main_pts"  : main_points,
            "il_pts"    : il_points,
            "total_runs": total_runs
        }
    
    def get_country(self, obj):
        if obj.countrycode:
            return obj.countrycode.name
        else:
            return None
        
    def get_awards(self, obj):
        if obj.awards:
            return AwardSerializer(obj.awards, many=True).data
        else:
            return None
    
    def to_representation(self, instance):
        return super().to_representation(instance)
    
    class Meta:
        model  = Players
        fields = ["id", "name", "nickname", "url", "country", "pronouns", "twitch", 
                "youtube", "twitter", "ex_stream", "awards", "stats"
        ]

### Used with the /games/ endpoint.
class GameSerializer(serializers.ModelSerializer):
    categories  = serializers.SerializerMethodField()
    levels      = serializers.SerializerMethodField()
    platforms   = serializers.SerializerMethodField()

    def get_categories(self, obj):
        if "categories" in self.context.get("embed", []):
            return CategorySerializer(Categories.objects.filter(game=obj), many=True).data
        else:
            return None
    
    def get_levels(self, obj):
        if "levels" in self.context.get("embed", []):
            return LevelSerializer(Levels.objects.filter(game=obj), many=True).data
        else:
            return None
    
    def get_platforms(self, obj):
        if "platforms" in self.context.get("embed", []):
            return PlatformSerializer(obj.platforms, many=True).data
        else:
            return None
        
    def to_representation(self, instance):
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
        model  = Games
        fields = ["id", "name", "slug", "release", "boxart", "twitch", "defaulttime",
                "idefaulttime", "pointsmax", "ipointsmax", "categories", "levels", "platforms"
        ]

### Used with the /levels/ endpoint.
class LevelSerializer(serializers.ModelSerializer):
    game = serializers.SerializerMethodField()

    def get_game(self, obj):
        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id)).data
        else:
            return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed", [])

        if "game" not in embed_fields:
            data.pop("game", None)

        return data
    
    class Meta:
        model  = Levels
        fields = ["id", "name", "url", "game"]

### Used with the /categories/ endpoint.
class CategorySerializer(serializers.ModelSerializer):
    game        = serializers.SerializerMethodField()
    variables   = serializers.SerializerMethodField()

    def get_game(self, obj):
        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id)).data
        else:
            return None
    
    def get_variables(self, obj):
        if "variables" in self.context.get("embed", []):
            return VariableSerializer(Variables.objects.filter(cat=obj.id), many=True).data
        else:
            return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed", [])

        if "game" not in embed_fields:
            data.pop("game", None)

        if "variables" not in embed_fields:
            data.pop("variables", None)

        return data
    
    class Meta:
        model  = Categories
        fields = ["id", "name", "type", "url", "hidden", "game", "variables"]

### Used with the /variables/ endpoint.
class VariableSerializer(serializers.ModelSerializer):
    game    = serializers.SerializerMethodField()
    values  = serializers.SerializerMethodField()

    def get_game(self, obj):
        if "game" in self.context.get("embed", []):
            return GameSerializer(Games.objects.filter(id=obj.game.id), many=True).data
        else:
            return None

    def get_values(self, obj):
        if "values" in self.context.get("embed", []):
            return ValueSerializer(VariableValues.objects.filter(var=obj.id), many=True).data
        else:
            return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed", [])

        if "game" not in embed_fields:
            data.pop("game", None)

        if "values" not in embed_fields:
            data.pop("values", None)

        return data
    
    class Meta:
        model  = Variables
        fields = ["id", "name", "cat", "all_cats", "scope", "hidden", "game", "values"]

### Used with the /values/ endpoint.
class ValueSerializer(serializers.ModelSerializer):
    variable = serializers.SerializerMethodField()

    def get_variable(self, obj):
        if "variable" in self.context.get("embed", []):
            return VariableSerializer(Variables.objects.get(id=obj.var.id)).data
        else:
            return obj.var.id
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        return data
    
    class Meta:
        model  = VariableValues
        fields = ["value", "name", "hidden", "variable"]

class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Awards
        fields = ["name"]

class StreamSerializer(serializers.ModelSerializer):
    streamer  = serializers.SerializerMethodField()
    game      = serializers.SerializerMethodField()

    def get_streamer(self, obj):
        return {
            "player"    : obj.streamer.name,
            "twitch"    : obj.streamer.twitch,
            "youtube"   : obj.streamer.youtube,
        }
    
    def get_game(self, obj):
        return {
            "id"      : obj.game.id,
            "name"    : obj.game.name,
            "twitch"  : obj.game.twitch,
        }

    class Meta:
        model  = NowStreaming
        fields = ["streamer", "game", "title", "offline_ct", "stream_time"]

class StreamSerializerPost(serializers.ModelSerializer):
    streamer    = serializers.CharField()
    game        = serializers.CharField()
    title       = serializers.CharField()
    offline_ct  = serializers.IntegerField()
    stream_time = serializers.CharField()

    def validate_streamer(self, streamer):
        try:
            return Players.objects.get(Q(id__iexact=streamer) | Q(name__iexact=streamer) | Q(twitch__icontains=streamer))
        except Players.DoesNotExist:
            raise serializers.ValidationError("streamer name or ID does not exist.")
        
    def validate_game(self, gameid):
        try:
            return Games.objects.get(Q(id__iexact=gameid) | Q(name__iexact=gameid) | Q(slug__iexact=gameid))
        except Games.DoesNotExist:
            raise serializers.ValidationError("game name, ID, or slug/abbreviation does not exist.")
        
    def validate_title(self, title):
        if len(title) == 0 or len(title) > 100:
            raise serializers.ValidationError("title length is 0 or greater than 100.")
        else:
            return title
    
    def validate_offline_ct(self, count):
        try:
            if count < 0:
                raise serializers.ValidationError("offline_ct must be a positive integer.")
            else:
                return count
        except Exception:
            raise serializers.ValidationError("offline_ct must be an integer.")
        
    def validate_stream_time(self, streamtime):
        try:
            correct_time = datetime.fromisoformat(streamtime.replace("Z", "+00:00")).replace(tzinfo=None)
            if correct_time > datetime.now():
                raise serializers.ValidationError("stream_time cannot be in the future.")
            else:
                return correct_time
        except Exception:
            raise serializers.ValidationError("Invalid date time format --- Example: '2024-12-31T06:23:51.188Z'")
    
    class Meta: 
        model  = NowStreaming
        fields = ["streamer", "game", "title", "offline_ct", "stream_time"]