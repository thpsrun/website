"""
######################################################################################################################################################
### File Name: api/serializers.py
### Author: ThePackle
### Description: Serializers used when an API endpoint is called.
### Dependencies: srl/models.py
######################################################################################################################################################
"""

from rest_framework import serializers
from srl.models import GameOverview,MainRuns,ILRuns,Players,Categories,Platforms,Levels,Variables,VariableValues,CountryCodes,Awards
from django.db.models import Q

### Used with the /import/ endpoint.
class ImportRunSerializer(serializers.Serializer):
    runid = serializers.CharField(max_length=10)

    """ def validate_runid(self, value):
        if not value:
            raise serializers.ValidationError("runid is required")
        return value """

### API Serializers
class MainRunSerializer(serializers.ModelSerializer):
    games      = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    platforms  = serializers.SerializerMethodField()

    def get_games(self,obj):
        if "games" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.filter(id=obj.game.id),many=True).data
        else:
            return None
        
    def get_categories(self,obj):
        if "categories" in self.context.get("embed",[]):
            return CategorySerializer(Categories.objects.filter(id=obj.category.id),many=True).data
        else:
            return None

    def get_platforms(self,obj):
        if "platforms" in self.context.get("embed",[]):
            return PlatformSerializer(Platforms.objects.filter(id=obj.platform.id),many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "games" not in embed_fields:
            data.pop("games",None)
        
        if "categories" not in embed_fields:
            data.pop("categories",None)
        
        if "platforms" not in embed_fields:
            data.pop("platforms",None)

        return data

    class Meta:
        model  = MainRuns
        fields = ["id","category","subcategory","place","values","player","player2","url","video","arch_video","date","v_date","time","time_secs","timenl","timenl_secs","timeigt","timeigt_secs","points","emulated","vid_status","obsolete","games","categories","platforms"]

class ILRunSerializer(serializers.ModelSerializer):
    games      = serializers.SerializerMethodField()
    levels     = serializers.SerializerMethodField()
    platforms  = serializers.SerializerMethodField()

    def get_games(self,obj):
        if "games" in self.context.get("embed",[]):
            return GameSerializer(GameOverview.objects.filter(id=obj.game.id),many=True).data
        else:
            return None
        
    def get_levels(self,obj):
        if "levels" in self.context.get("embed",[]):
            return LevelSerializer(Levels.objects.filter(game=obj.game.id),many=True).data
        else:
            return None
        
    def get_platforms(self,obj):
        if "platforms" in self.context.get("embed",[]):
            return PlatformSerializer(Platforms.objects.filter(id=obj.platform),many=True).data
        else:
            return None
    
    def to_representation(self,instance):
        data = super().to_representation(instance)
        embed_fields = self.context.get("embed",[])

        if "games" not in embed_fields:
            data.pop("games",None)
        
        if "categories" not in embed_fields:
            data.pop("categories",None)
        
        if "platforms" not in embed_fields:
            data.pop("platforms",None)

        return data

    class Meta:
        model  = ILRuns
        fields = ["id","category","subcategory","place","values","player","url","video","arch_video","date","v_date","time","time_secs","timenl","timenl_secs","timeigt","timeigt_secs","points","emulated","vid_status","obsolete","games","levels","platforms"]

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
        fields = ["id","name","abbr","release","boxart","defaulttime","idefaulttime","pointsmax","ipointsmax","categories","levels","platforms"]

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