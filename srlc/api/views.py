from rest_framework.views import APIView
from django.http import HttpResponseForbidden,HttpResponseBadRequest,HttpResponseServerError,HttpResponseNotFound,HttpResponse
from rest_framework.response import Response
from .serializers import APIProcessRunsSerializer,APIPlayersSerializer,APIGamesSerializer,APICategoriesSerializer,APIVariablesSerializer,APIValuesSerializer,APILevelsSerializer,APINewRunsSerializer,APINewWRsSerializer
from srl.tasks import *
from srl.models import GameOverview,MainRuns,ILRuns,NewRuns,NewWRs
from srl.models import *
from api.tasks import *
from django.db.models import Count,F,Subquery,OuterRef, Q

class API_ProcessRuns(APIView):
    def get(self,request,runid=None):
        return HttpResponseBadRequest("GET Requests are not allowed")

    def post(self, request, runid):
        serializer = APIProcessRunsSerializer(data={"runid": runid})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_runid = validated_data["runid"]

        run_info = src_api(f"https://speedrun.com/api/v1/runs/{validated_runid}?embed=players")

        if "speedrun.com/th" in run_info["weblink"]:
            if not GameOverview.objects.filter(id=run_info["game"]).exists():
                update_game_runs(run_info["game"])
            else:
                if run_info["level"]:
                    lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run_info['game']}/level/{run_info['level']}/{run_info['category']}?embed=game,category,level,players,variables")

                    update_level(lb_info["level"]["data"],run_info["game"])
                elif len(run_info["values"]) > 0:
                    lb_variables = ""
                    for key, value in run_info["values"].items():
                        lb_variables += f"var-{key}={value}&"

                    lb_variables = lb_variables.rstrip("&")

                    lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run_info['game']}/category/{run_info['category']}?{lb_variables}&embed=game,category,level,players,variables")
                else:
                    lb_info = src_api(f"https://speedrun.com/api/v1/leaderboards/{run_info['game']}/category/{run_info['category']}?embed=game,category,level,players,variables")
                
                for variable in lb_info["variables"]["data"]:
                    update_variable(run_info["game"],variable)

                update_category(lb_info["category"]["data"],run_info["game"])
                for run in lb_info["runs"]:
                    if run["run"]["id"] == run_info["id"]:
                        add_run(lb_info["game"]["data"],run,lb_info["category"]["data"],lb_info["level"]["data"],run_info["values"])

                        player_check = run_info.get("players").get("data")[0].get("rel") if run_info.get("players").get("data") else run_info.get("players")[0].get("rel")
                        if player_check != "guest":
                            if run_info["level"]:
                                try: rank = ILRuns.objects.filter(id=run_info["id"]).values("place")[0]["place"]
                                except: rank = 1
                            else:
                                try: rank = MainRuns.objects.filter(id=run_info["id"]).values("place")[0]["place"]
                                except: rank = 1

                            if rank == 1:
                                with transaction.atomic():
                                    run, created = NewWRs.objects.update_or_create(
                                        id=run_info["id"],
                                        defaults={
                                            "timeadded": run_info["status"]["verify-date"],
                                        }
                                    )
                                    if not created:
                                        run.id = run_info["id"]
                                        run.timeadded = run_info["status"]["verify-date"]
                                        run.save()
                            else:
                                with transaction.atomic():
                                    run, created = NewRuns.objects.update_or_create(
                                        id=run_info["id"],
                                        defaults={
                                            "timeadded": run_info["status"]["verify-date"],
                                        }
                                    )
                                    if not created:
                                        run.id = run_info["id"]
                                        run.timeadded = run_info["status"]["verify-date"]
                                        run.save()

                        return HttpResponse(status=200)
                    else:
                        run_info["place"] = 0
                        add_run(lb_info["game"]["data"],run_info,lb_info["category"]["data"],lb_info["level"]["data"],run_info["values"],True)
                        return HttpResponse(status=200)
        else:
            return HttpResponse("The run provided is not associated with the Tony Hawk series.")

class API_Runs(APIView):
    def get(self, request, runid):
        serializer = APIProcessRunsSerializer(data={"runid": runid})
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
    def get(self, request, player):
        serializer = APIPlayersSerializer(data={"player": player})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_player = validated_data["player"]

        if validated_player != "all":
            try:
                player_data = Players.objects.filter(Q(id__iexact=validated_player) | Q(name__iexact=validated_player))[0]
            except:
                player_data = None

        if validated_player == "all":
            players = Players.objects.filter().values_list("id","name","pronouns","twitch","youtube")

            return Response({
                "players":              players,
            })
        elif not player_data:
            return HttpResponseNotFound(f"player name or id {validated_player} does not exist.")
        else:
            main_runs    = MainRuns.objects.filter(Q(playerid=player_data.id) | Q(playerid2=player_data.id)).filter(points__gt=0)
            il_runs      = ILRuns.objects.filter(playerid=player_data.id).filter(points__gt=0)

            main_points  = sum(run.points for run in main_runs)
            il_points    = sum(run.points for run in il_runs)
            total_points =  main_points + il_points

            total_runs = len(main_runs) + len(il_runs)
            
            return Response({
                "id":                   player_data.id,
                "name":                 player_data.name,
                "url":                  player_data.url,
                "total_packlepoints":   total_points,
                "fg_packlepoints":      main_points,
                "il_packlepoints":      il_points,
                "total_runs":           total_runs,
                "pronouns":             player_data.pronouns,
                "twitch":               player_data.twitch,
                "youtube":              player_data.youtube,
                "twitter":              player_data.twitter,
            })

class API_Games(APIView):
    def get(self, request, game):
        serializer = APIGamesSerializer(data={"game": game})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_game = validated_data["game"]

        game_data = GameOverview.objects.filter(Q(id=validated_game) | Q(abbr=validated_game))

        if len(game_data) == 0:
            return HttpResponseNotFound(f"game abbreviation or id {game_data} does not exist.")
        else:
            return Response({
                "id":           game_data[0].id,
                "name":         game_data[0].name,
                "abbr":         game_data[0].abbr,
                "release":      game_data[0].release,
                "defaulttime":  game_data[0].defaulttime
            })
            
class API_Categories(APIView):
    def get(self, request, cat):
        serializer = APICategoriesSerializer(data={"category": cat})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_cat  = validated_data["category"]

        category_data = Categories.objects.filter(Q(id=validated_cat) | Q(name=validated_cat))

        if len(category_data) == 0:
            return HttpResponseNotFound(f"category name or id {category_data} does not exist.")
        else:
            return Response({
                "id":       category_data[0].id,
                "gameid":   category_data[0].game,
                "name":     category_data[0].name,
                "type":     category_data[0].type,
            })
            
class API_Variables(APIView):
    def get(self, request, variable):
        serializer = APIVariablesSerializer(data={"variable": variable})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_var  = validated_data["variable"]

        variable_data = Variables.objects.filter(Q(id=validated_var) | Q(name=validated_var))

        if len(variable_data) == 0:
            return HttpResponseNotFound(f"variable name or id {variable_data} does not exist.")
        else:
            return Response({
                "id":       variable_data[0].id,
                "gameid":   variable_data[0].game,
                "name":     variable_data[0].name,
                "category": variable_data[0].cat,
                "scope":    variable_data[0].scope,
            })

class API_Values(APIView):
    def get(self, request, value):
        serializer = APIValuesSerializer(data={"value": value})
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
     def get(self, request, level):
        serializer = APILevelsSerializer(data={"level": level})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validate_level = validated_data["level"]

        levels_data = Levels.objects.filter(id=validate_level)

        if len(levels_data) == 0:
            return HttpResponseNotFound(f"level id {validate_level} does not exist.")
        else:
            return Response({
                "id":       levels_data[0].id,
                "gameid":   levels_data[0].game,
                "name":     levels_data[0].name,
            })

class API_NewRuns(APIView):
    def get(self, request, newruns):
        serializer = APINewRunsSerializer(data={"newruns": newruns})
        serializer.is_valid(raise_exception=True)

        validated_data   = serializer.validated_data
        validate_newruns = validated_data["newruns"]

        newruns_data = NewRuns.objects.filter(id=validate_newruns)

        if len(newruns_data) == 0:
            return HttpResponseNotFound(f"newrun id {newruns_data} does not exist.")
        else:
            return Response({
                "id":        newruns_data[0].id,
                "timeadded": newruns_data[0].timeadded,
            })
            
class API_NewWRs(APIView):
    def get(self, request, newwrs):
        serializer = APINewWRsSerializer(data={"newwrs": newwrs})
        serializer.is_valid(raise_exception=True)

        validated_data   = serializer.validated_data
        validate_newwrs  = validated_data["newwrs"]

        newwrs_data = NewWRs.objects.filter(id=validate_newwrs)

        if len(newwrs_data) == 0:
            return HttpResponseNotFound(f"newwrs id {newwrs_data} does not exist.")
        else:
            return Response({
                "id":        newwrs_data[0].id,
                "timeadded": newwrs_data[0].timeadded,
            })