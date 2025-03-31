from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseForbidden,HttpResponseBadRequest,HttpResponseServerError,HttpResponseNotFound,HttpResponse
from .serializers import *
from srl.tasks import *
from srl.models import GameOverview,MainRuns,ILRuns
from api.tasks import *
from django.db.models import Count,F,Subquery,OuterRef, Q
from django.http import JsonResponse

class API_ProcessRuns(APIView):
    def get(self,request,runid=None):
        return HttpResponseBadRequest("GET Requests are not allowed")

    def post(self, request, runid):
        serializer = ImportRunSerializer(data={"runid": runid})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_runid = validated_data["runid"]

        run_info = src_api(f"https://speedrun.com/api/v1/runs/{validated_runid}?embed=players")

        if "speedrun.com/th" in run_info["weblink"]:
            if not GameOverview.objects.filter(id=run_info["game"]).exists():
                update_game_runs.delay(run_info["game"])

            for player in run_info["players"]["data"]:
                if player["rel"] != "guest":
                    if not Players.objects.filter(id=player["id"]).exists():
                        update_player.delay(player["id"])

            if run_info["level"]:
                lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run_info['game']}/level/{run_info['level']}/{run_info['category']}?embed=game,category,level,players,variables")

                update_level.delay(lb_info["level"]["data"],run_info["game"])
            elif len(run_info["values"]) > 0:
                lb_variables = ""
                for key, value in run_info["values"].items():
                    lb_variables += f"var-{key}={value}&"

                lb_variables = lb_variables.rstrip("&")

                lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run_info['game']}/category/{run_info['category']}?{lb_variables}&embed=game,category,level,players,variables")
            else:
                lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run_info['game']}/category/{run_info['category']}?embed=game,category,level,players,variables")
            
            for variable in lb_info["variables"]["data"]:
                update_variable.delay(run_info["game"],variable)

            update_category.delay(lb_info["category"]["data"],run_info["game"])
            finish = 0
            for run in lb_info["runs"]:
                if run["run"]["id"] == run_info["id"]:
                    add_run.delay(lb_info["game"]["data"],run,lb_info["category"]["data"],lb_info["level"]["data"],run_info["values"])
                    finish = 1
                
            if finish == 0:
                run_info["place"] = 0
                add_run.delay(lb_info["game"]["data"],run_info,lb_info["category"]["data"],lb_info["level"]["data"],run_info["values"],True)
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=200)
        else:
            return HttpResponse("The run provided is not associated with the Tony Hawk series.")

class API_Runs(APIView):
    def get(self, request, runid):
        serializer = ImportRunSerializer(data={"runid": runid})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_runid = validated_data["runid"]

        run = MainRuns.objects.filter(id=validated_runid) or ILRuns.objects.filter(id=validated_runid)

        if len(run) == 0:
            return HttpResponseNotFound(f"runid {validated_runid} does not exist in either FG or IL models.")
        else:
            common = {
                "id":           run[0].id,
                "gameid":       run[0].game,
                "category":     run[0].category,
                "subcategory":  run[0].subcategory,
                "values":       run[0].values,
                "place":        run[0].place,
                "url":          run[0].url,
                "date":         run[0].date,
                "time":         run[0].time,
                "time_secs":    run[0].time_secs,
                "packlepoints": run[0].points,
                "platform":     run[0].platform,
                "player1":      run[0].player,
            }

            try:
                common["player2"] = run[0].playerid2
            except AttributeError:
                common["levelid"] = run[0].levelid

            return Response(common)
                
    def post(self,request,runid=None):
        return HttpResponseBadRequest("POST Requests are not allowed")
    
    def update(self,request,runid=None):
        return HttpResponseBadRequest("POST Requests are not allowed")
    
class API_Players(APIView):
    ALLOWED_QUERIES = {"streamexceptions"}
    def get(self,request,id):
        query_fields    = request.GET.get("query","").split(",")
        query_fields    = [field.strip() for field in query_fields if field.strip()] 
        invalid_queries = [field for field in query_fields if field not in self.ALLOWED_QUERIES]

        if invalid_queries:
            return Response({"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},status=status.HTTP_400_BAD_REQUEST)

        if id == "all":
            players = Players.objects.all()

            if "streamexceptions" in query_fields:
                players = players.filter(ex_stream=True)

            return Response(PlayerSerializer(players,many=True).data)

        player = Players.objects.filter(id__iexact=id).first() or Players.objects.filter(name__iexact=id).first()
        if player:
            return Response(PlayerSerializer(player).data)
        else:
            return Response({"ERROR": "Player ID or Name does not exist."}, status=status.HTTP_404_NOT_FOUND)

class API_PlayerRecords(APIView):
    ALLOWED_EMBEDS = {"categories","levels","games","platforms"}
    def get(self,request,id):
        embed_fields   = request.GET.get("embed","").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},status=status.HTTP_400_BAD_REQUEST)

        player = Players.objects.filter(id__iexact=id).first() or Players.objects.filter(name__iexact=id).first()
        if player:
            player_data = PlayerSerializer(player).data

            main_runs = MainRuns.objects.filter(player=player).filter(obsolete=False)
            il_runs   = ILRuns.objects.filter(player=player).filter(obsolete=False)

            main_data = MainRunSerializer(main_runs,many=True,context={"embed": embed_fields}).data
            il_data   = ILRunSerializer(il_runs,many=True,context={"embed": embed_fields}).data

            return Response({
                **player_data,
                "main_runs" : main_data,
                "il_runs"   : il_data
            })
        else:
            return Response({"ERROR": "Player ID or Name does not exist."}, status=status.HTTP_404_NOT_FOUND)

class API_Games(APIView):
    ALLOWED_EMBEDS = {"categories","levels","platforms"}
    def get(self,request,id):
        if len(id) > 15:
            return Response({"ERROR": f"Game ID exceeds maximum length."},status=status.HTTP_400_BAD_REQUEST)

        embed_fields   = request.GET.get("embed","").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},status=status.HTTP_400_BAD_REQUEST)

        if id == "all":
            games = GameOverview.objects.all().order_by("release")
            return Response(GameSerializer(games,many=True,context={"embed": embed_fields}).data)
        
        game = GameOverview.objects.filter(id__iexact=id).first() or GameOverview.objects.filter(abbr__iexact=id).first()
        if game:
            return Response(GameSerializer(game,context={"embed": embed_fields}).data)
        else:
            return Response({"ERROR": "Game ID or Abbreviation does not exist"}, status=status.HTTP_404_NOT_FOUND)

class API_Categories(APIView):
    ALLOWED_EMBEDS = {"games","variables"}
    def get(self,request,id):
        if len(id) > 15:
            return Response({"ERROR": f"Category ID exceeds maximum length."},status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed","").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},status=status.HTTP_400_BAD_REQUEST)
    
        category = Categories.objects.filter(id__iexact=id).first()
        if category:
            return Response(CategorySerializer(category,context={"embed": embed_fields}).data) 
        else:
            return Response({"ERROR": "Category ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
class API_Variables(APIView):
    ALLOWED_EMBEDS = {"games","values"}
    def get(self,request,id):
        if len(id) > 15:
            return Response({"ERROR": f"Variable ID exceeds maximum length."},status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed","").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},status=status.HTTP_400_BAD_REQUEST)
    
        variables = Variables.objects.filter(id__iexact=id).first()
        if variables:
            return Response(VariableSerializer(variables,context={"embed": embed_fields}).data) 
        else:
            return Response({"ERROR": "Variable ID does not exist"}, status=status.HTTP_404_NOT_FOUND)

class API_Values(APIView):
    def get(self, request, value):
        serializer = ValueSerializer(data={"value": value})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validate_val   = validated_data["value"]

        values_data = VariableValues.objects.filter(valueid=validate_val)

        if len(values_data) == 0:
            return HttpResponseNotFound(f"value id {validate_val} does not exist.")
        else:
            return Response({
                "var":      values_data[0].var,
                "valueid":  values_data[0].value,
                "name":     values_data[0].name,
            })
            
class API_Levels(APIView):
    ALLOWED_EMBEDS = {"games"}
    def get(self,request,id):
        if len(id) > 15:
            return Response({"ERROR": f"Level ID exceeds maximum length."},status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed","").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},status=status.HTTP_400_BAD_REQUEST)
    
        levels = Levels.objects.filter(id__iexact=id).first()
        if levels:
            return Response(LevelSerializer(levels,context={"embed": embed_fields}).data) 
        else:
            return Response({"ERROR": "Level ID does not exist"}, status=status.HTTP_404_NOT_FOUND)