from rest_framework import serializers

class APIProcessRunsSerializer(serializers.Serializer):
    runid = serializers.CharField(max_length=10)

    def validate_runid(self, value):
        if not value:
            raise serializers.ValidationError("runid is required")
        return value
    
class APIPlayersSerializer(serializers.Serializer):
    player = serializers.CharField(max_length=25)

    def validate_player(self, value):
        if not value:
            raise serializers.ValidationError("player name or id is required")
        return value

class APIGamesSerializer(serializers.Serializer):
    game = serializers.CharField(max_length=25)

    def validate_game(self, value):
        if not value:
            raise serializers.ValidationError("game abbreviation or id is required")
        return value
    
class APICategoriesSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=10)

    def validate_category(self, value):
        if not value:
            raise serializers.ValidationError("category name or id is required")
        return value
    
class APIVariablesSerializer(serializers.Serializer):
    variable = serializers.CharField(max_length=25)

    def validate_variables(self, value):
        if not value:
            raise serializers.ValidationError("variable id is required")
        return value
    
class APIValuesSerializer(serializers.Serializer):
    value = serializers.CharField(max_length=10)

    def validate_values(self, value):
        if not value:
            raise serializers.ValidationError("value id is required")
        return value
    
class APILevelsSerializer(serializers.Serializer):
    level = serializers.CharField(max_length=10)

    def validate_levels(self, value):
        if not value:
            raise serializers.ValidationError("level id is required")
        return value
    
class APINewRunsSerializer(serializers.Serializer):
    newruns = serializers.CharField(max_length=10)

    def validate_newruns(self, value):
        if not value:
            raise serializers.ValidationError("newrun id is required")
        return value
    
class APINewWRsSerializer(serializers.Serializer):
    newwrs = serializers.CharField(max_length=10)

    def validate_newwrs(self, value):
        if not value:
            raise serializers.ValidationError("newwr id is required")
        return value