"""
######################################################################################################################################################
### File Name: api/serializers.py
### Author: ThePackle
### Description: Serializers used when an API endpoint is called.
### Dependencies: srl/models.py
######################################################################################################################################################
"""

from rest_framework import serializers
from datetime import datetime
from srl.models import GameOverview,MainRuns,ILRuns,Players,Categories,Platforms,Levels,Variables,VariableValues,CountryCodes,Awards,NowStreaming
from django.db.models import Q

### Used with the /import/ endpoint.
class ImportRunSerializer(serializers.Serializer):
    runid = serializers.CharField(max_length=10)

    def validate_runid(self, value):
        if not value:
            raise serializers.ValidationError("runid is required")
        return value

### API Serializers
class MainRunSerializer(serializers.ModelSerializer):
    game       = serializers.SerializerMethodField()
    category   = serializers.SerializerMethodField()
    platform   = serializers.SerializerMethodField()
    time       = serializers.SerializerMethodField()
    players    = serializers.SerializerMethodField()

    def get_game(self,obj):
        if "game" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.get(id=obj.game.id)).data
        else:
            return obj.game.id
        
    def get_category(self,obj):
        if "category" in self.context.get("embed",[]):
            return CategorySerializer(Categories.objects.get(id=obj.category.id)).data
        else:
            return obj.category.id

    def get_platform(self,obj):
        if "platform" in self.context.get("embed",[]):
            return PlatformSerializer(Platforms.objects.get(id=obj.platform.id)).data
        else:
            return obj.platform.id
        
    def get_time(self,obj):
        return ({
            "defaulttime": obj.game.defaulttime,
            "time":obj.time,
            "time_secs":obj.time_secs,
            "timenl":obj.timenl,
            "timenl_secs":obj.timenl_secs,
            "timeigt":obj.timeigt,
            "timeigt_secs":obj.timeigt_secs
        })
        
    def get_players(self,obj):
        if "players" in self.context.get("embed",[]):
            player1 = PlayerSerializer(Players.objects.get(id=obj.player.id)).data

            if obj.player2:
                player2 = PlayerSerializer(Players.objects.get(id=obj.player2.id)).data
                return player1,player2
            else:
                return player1
        else:
            if obj.player2:
                return obj.player.id,obj.player2.id
            else:
                return obj.player.id
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        data.pop("player",None)
        data.pop("player2",None)
        data.pop("time_secs",None)
        data.pop("timenl",None)
        data.pop("timenl_secs",None)
        data.pop("timeigt",None)
        data.pop("timeigt_secs",None)

        return data

    class Meta:
        model  = MainRuns
        fields = ["id","game","platform","category","subcategory","place","values","player","player2","players","url","video","arch_video","date","v_date","time","time_secs","timenl","timenl_secs","timeigt","timeigt_secs","points","emulated","vid_status","obsolete"]

class ILRunSerializer(serializers.ModelSerializer):
    game       = serializers.SerializerMethodField()
    level      = serializers.SerializerMethodField()
    platform   = serializers.SerializerMethodField()
    time       = serializers.SerializerMethodField()
    players    = serializers.SerializerMethodField()

    def get_game(self,obj):
        if "game" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.get(id=obj.game.id)).data
        else:
            return obj.game.id
        
    def get_level(self,obj):
        if any(e in self.context.get("embed",[]) for e in ["category", "level"]):            
            return LevelSerializer(Levels.objects.get(id=obj.level.id)).data
        else:
            return obj.level.id
        
    def get_platform(self,obj):
        if "platform" in self.context.get("embed",[]):
            return PlatformSerializer(Platforms.objects.get(id=obj.platform.id)).data
        else:
            return obj.platform.id
        
    def get_time(self,obj):
        return ({
            "defaulttime": obj.game.idefaulttime,
            "time":obj.time,
            "time_secs":obj.time_secs,
            "timenl":obj.timenl,
            "timenl_secs":obj.timenl_secs,
            "timeigt":obj.timeigt,
            "timeigt_secs":obj.timeigt_secs
        })
    
    def get_players(self,obj):
        if "players" in self.context.get("embed",[]):
            player1 = PlayerSerializer(Players.objects.get(id=obj.player.id)).data

            return [player1]
        else:
            return [obj.player.id]
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        data.pop("player",None)
        data.pop("time_secs",None)
        data.pop("timenl",None)
        data.pop("timenl_secs",None)
        data.pop("timeigt",None)
        data.pop("timeigt_secs",None)

        return data

    class Meta:
        model  = ILRuns
        fields = ["id","game","platform","level","subcategory","place","values","player","players","url","video","arch_video","date","v_date","time","time_secs","timenl","timenl_secs","timeigt","timeigt_secs","points","emulated","vid_status","obsolete"]

### Used with the /platform/ endpoint.
class PlatformSerializer(serializers.ModelSerializer):
    games = serializers.SerializerMethodField()

    def get_games(self,obj):
        if "games" in self.context.get("embed",[]):
            return GameSerializer(obj.game).data if obj.game else None
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "games" not in embed_fields:
            data.pop("games",None)

        return data
    
    class Meta:
        model  = Platforms
        fields = ["id","name","games"]

### Used with the /players/ endpoint
class PlayerSerializer(serializers.ModelSerializer):
    stats   = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    awards  = serializers.SerializerMethodField()

    def get_stats(self,obj):
        main_runs   = MainRuns.objects.filter(Q(player=obj.id) | Q(player2=obj.id)).filter(points__gt=0)
        il_runs     = ILRuns.objects.filter(player=obj.id).filter(points__gt=0)

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
    
    def get_country(self,obj):
        if obj.countrycode:
            return obj.countrycode.name
        else:
            return None
        
    def get_awards(self,obj):
        if obj.awards:
            return AwardSerializer(obj.awards,many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        return super().to_representation(instance)
    
    class Meta:
        model  = Players
        fields = ["id","name","nickname","url","country","pronouns","twitch","youtube","twitter","ex_stream","awards","stats"]

### Used with the /games/ endpoint.
class GameSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    levels     = serializers.SerializerMethodField()
    platforms  = serializers.SerializerMethodField()

    def get_categories(self,obj):
        if "categories" in self.context.get("embed",[]):
            return CategorySerializer(Categories.objects.filter(game=obj),many=True).data
        else:
            return None
    
    def get_levels(self,obj):
        if "levels" in self.context.get("embed",[]):
            return LevelSerializer(Levels.objects.filter(game=obj),many=True).data
        else:
            return None
    
    def get_platforms(self,obj):
        if "platforms" in self.context.get("embed",[]):
            return PlatformSerializer(obj.platforms,many=True).data
        else:
            return None
        
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "categories" not in embed_fields:
            data.pop("categories",None)

        if "levels" not in embed_fields:
            data.pop("levels",None)
        
        if "platforms" not in embed_fields:
            data.pop("platforms",None)

        return data
        
    class Meta:
        model  = GameOverview
        fields = ["id","name","abbr","release","boxart","twitch","defaulttime","idefaulttime","pointsmax","ipointsmax","categories","levels","platforms"]

### Used with the /levels/ endpoint.
class LevelSerializer(serializers.ModelSerializer):
    games = serializers.SerializerMethodField()

    def get_games(self,obj):
        if "games" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.filter(id=obj.game.id),many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "games" not in embed_fields:
            data.pop("games",None)

        return data
    
    class Meta:
        model  = Levels
        fields = ["id","name","url","games"]

### Used with the /categories/ endpoint.
class CategorySerializer(serializers.ModelSerializer):
    games     = serializers.SerializerMethodField()
    variables = serializers.SerializerMethodField()

    def get_games(self,obj):
        if "games" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.filter(id=obj.game.id),many=True).data
        else:
            return None
    
    def get_variables(self,obj):
        if "variables" in self.context.get("embed",[]):
            return VariableSerializer(Variables.objects.filter(cat=obj.id),many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "games" not in embed_fields:
            data.pop("games",None)

        if "variables" not in embed_fields:
            data.pop("variables",None)

        return data
    
    class Meta:
        model  = Categories
        fields = ["id","name","type","url","hidden","games","variables"]

### Used with the /variables/ endpoint.
class VariableSerializer(serializers.ModelSerializer):
    games  = serializers.SerializerMethodField()
    values = serializers.SerializerMethodField()

    def get_games(self,obj):
        if "games" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.filter(id=obj.game.id),many=True).data
        else:
            return None

    def get_values(self,obj):
        if "values" in self.context.get("embed",[]):
            return ValueSerializer(VariableValues.objects.filter(var=obj.id),many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "games" not in embed_fields:
            data.pop("games",None)

        if "values" not in embed_fields:
            data.pop("values",None)

        return data
    
    class Meta:
        model  = Variables
        fields = ["id","name","cat","all_cats","scope","hidden","games","values"]

### Used with the /values/ endpoint.
class ValueSerializer(serializers.ModelSerializer):
    variables = serializers.SerializerMethodField()

    def get_variables(self,obj):
        if "variables" in self.context.get("embed",[]):
            return VariableSerializer(VariableSerializer.objects.filter(cat=obj.cat),many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "variables" not in embed_fields:
            data.pop("variables",None)

        return data
    
    class Meta:
        model  = VariableValues
        fields = ["value","name","hidden","variables"]

class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Awards
        fields = ["name"]

class StreamSerializer(serializers.ModelSerializer):
    streamer  = serializers.SerializerMethodField()
    game      = serializers.SerializerMethodField()

    def get_streamer(self,obj):
        return {
            "player"    : obj.streamer.name,
            "twitch"    : obj.streamer.twitch,
            "youtube"   : obj.streamer.youtube,
        }
    
    def get_game(self,obj):
        return {
            "id"      : obj.game.id,
            "name"    : obj.game.name,
            "twitch"  : obj.game.twitch,
        }

    class Meta:
        model  = NowStreaming
        fields = ["streamer","game","title","offline_ct","stream_time"]

class StreamSerializerPost(serializers.ModelSerializer):
    streamer    = serializers.CharField()
    game        = serializers.CharField()
    title       = serializers.CharField()
    offline_ct  = serializers.IntegerField()
    stream_time = serializers.CharField()

    def validate_streamer(self,streamer):
        try:
            return Players.objects.get(Q(id__iexact=streamer) | Q(name__iexact=streamer))
        except Players.DoesNotExist:
            raise serializers.ValidationError("Player name or ID does not exist.")
        
    def validate_game(self,gameid):
        try:
            return GameOverview.objects.get(Q(id__iexact=gameid) | Q(name__iexact=gameid) | Q(abbr__iexact=gameid))
        except GameOverview.DoesNotExist:
            raise serializers.ValidationError("Game name, ID, or abbreviation does not exist.")
        
    def validate_title(self,title):
        if len(title) == 0 or len(title) > 100:
            raise serializers.ValidationError("Title length is 0 or greater than 100.")
        else:
            return title
    
    def validate_offline_ct(self,count):
        try:
            if count < 0:
                raise serializers.ValidationError("Offline count must be positive.")
            else:
                return count
        except:
            raise serializers.ValidationError("Offline count must be an integer.")
        
    def validate_stream_time(self,streamtime):
        try:
            correct_time = datetime.fromisoformat(streamtime.replace("Z","+00:00")).replace(tzinfo=None)
            if correct_time > datetime.now():
                raise serializers.ValidationError("Date and time cannot be in the future.")
            else:
                return correct_time
        except:
            raise serializers.ValidationError(f"Invalid date time format --- Example: '2024-12-31T06:23:51.188Z'")
    
    class Meta: 
        model  = NowStreaming
        fields = ["streamer","game","title","offline_ct","stream_time"]