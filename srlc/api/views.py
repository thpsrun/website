import time

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import (
    Categories,
    Games,
    Levels,
    NowStreaming,
    Players,
    Runs,
    Variables,
    VariableValues,
)

from api.tasks import normalize_src

from .serializers import (
    CategorySerializer,
    GameSerializer,
    LevelSerializer,
    PlayerSerializer,
    RunSerializer,
    StreamSerializer,
    StreamSerializerPost,
    ValueSerializer,
    VariableSerializer,
)


class API_Runs(APIView):
    ALLOWED_QUERIES = {"status"}
    ALLOWED_EMBEDS  = {"category", "level", "game", "variables", "platform", "players"}
    def get(self, request, id):
        query_fields    = request.GET.get("query", "").split(",")
        query_fields    = [field.strip() for field in query_fields if field.strip()] 
        invalid_queries = [field for field in query_fields if field not in self.ALLOWED_QUERIES]

        if invalid_queries:
            return Response({"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)

        if id == "all":
            if "status" in query_fields:
                new_runs = Runs.objects.filter(vid_status="new")
                runs = RunSerializer(new_runs, many=True, context={"embed": embed_fields}).data
                
                return Response({
                    "new_runs" : runs,
                })
            else:
                return Response({"ERROR": "'all' can only be used with a query (status)."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            run = Runs.objects.filter(id__iexact=id).first()
            if run:
                return Response(RunSerializer(run,context={"embed": embed_fields}).data, status=status.HTTP_200_OK)
            else:
                return Response({"ERROR": "run id provided does not exist."}, status=status.HTTP_200_OK)

    def post(self, request, id):
        if len(id) > 10:
            return Response({"ERROR": "id must be less than 10 characters."}, status=status.HTTP_400_BAD_REQUEST)
        
        normalize = normalize_src.delay(id)
        ilcheck = normalize.get()
        time.sleep(2) ### Sometimes the other celery tasks are slow, so this will allow them to quickly finish before providing a response.

        if ilcheck == "invalid":
            return Response({"ERROR": "id provided does not belong to this leaderboard's games."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            run = Runs.objects.filter(id=id).first()
            if run:
                return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)
            else:
                return Response({"ERROR": f"Unknown error - The run id {id} could not be called."}, status=status.HTTP_400_BAD_REQUEST)
              
    def put(self, request, id):
        if len(id) > 10:
            return Response({"ERROR": "id must be less than 10 characters."}, status=status.HTTP_400_BAD_REQUEST)
        
        normalize = normalize_src.delay(id)
        ilcheck = normalize.get()
        time.sleep(2) ### Sometimes the other celery tasks are slow, so this will allow them to quickly finish before providing a response.

        if ilcheck == "invalid":
            return Response({"ERROR": "id provided does not belong to this leaderboard's games."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            run = Runs.objects.filter(id=id).first()
            if run:
                return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)
            else:
                return Response({"ERROR": f"Unknown error - The run id {id} could not be called."}, status=status.HTTP_400_BAD_REQUEST)
    
class API_Players(APIView):
    ALLOWED_QUERIES = {"streamexceptions"}
    def get(self, request, id):
        query_fields    = request.GET.get("query", "").split(",")
        query_fields    = [field.strip() for field in query_fields if field.strip()] 
        invalid_queries = [field for field in query_fields if field not in self.ALLOWED_QUERIES]

        if invalid_queries:
            return Response({"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"}, status=status.HTTP_400_BAD_REQUEST)

        if id == "all":
            players = Players.objects.all()

            if "streamexceptions" in query_fields:
                players = players.filter(ex_stream=True)

            return Response(PlayerSerializer(players, many=True).data)

        player = Players.objects.filter(id__iexact=id).first() or Players.objects.filter(name__iexact=id).first()
        if player:
            return Response(PlayerSerializer(player).data)
        else:
            return Response({"ERROR": "Player ID or Name does not exist."}, status=status.HTTP_404_NOT_FOUND)

class API_PlayerRecords(APIView):
    ALLOWED_EMBEDS = {"categories", "levels", "games", "platforms"}
    def get(self, request, id):
        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)

        player = Players.objects.filter(id__iexact=id).first() or Players.objects.filter(name__iexact=id).first()
        if player:
            player_data = PlayerSerializer(player).data

            main_runs = Runs.objects.main().filter(player=player).filter(obsolete=False)
            il_runs   = Runs.objects.il().filter(player=player).filter(obsolete=False)

            main_data = RunSerializer(main_runs, many=True, context={"embed": embed_fields}).data
            il_data   = RunSerializer(il_runs, many=True, context={"embed": embed_fields}).data

            return Response({
                **player_data,
                "main_runs" : main_data,
                "il_runs"   : il_data
            })
        else:
            return Response({"ERROR": "Player ID or Name does not exist."}, status=status.HTTP_404_NOT_FOUND)

class API_Games(APIView):
    ALLOWED_EMBEDS = {"categories", "levels", "platforms"}
    def get(self, request, id):
        if len(id) > 15:
            return Response({"ERROR": "Game ID exceeds maximum length."}, status=status.HTTP_400_BAD_REQUEST)

        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)

        if id == "all":
            games = Games.objects.all().order_by("release")
            return Response(GameSerializer(games, many=True, context={"embed": embed_fields}).data, status=status.HTTP_200_OK)
        
        game = Games.objects.filter(id__iexact=id).first() or Games.objects.filter(slug__iexact=id).first()
        if game:
            return Response(GameSerializer(game, context={"embed": embed_fields}).data, status=status.HTTP_200_OK)
        else:
            return Response({"ERROR": "Game ID or slug/abbreviation does not exist"}, status=status.HTTP_404_NOT_FOUND)

class API_Categories(APIView):
    ALLOWED_EMBEDS = {"game", "variables"}
    def get(self, request, id):
        if len(id) > 15:
            return Response({"ERROR": "Category ID exceeds maximum length."}, status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)
    
        category = Categories.objects.filter(id__iexact=id).first()
        if category:
            return Response(CategorySerializer(category, context={"embed": embed_fields}).data, status=status.HTTP_200_OK) 
        else:
            return Response({"ERROR": "Category ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
class API_Variables(APIView):
    ALLOWED_EMBEDS = {"game", "values"}
    def get(self, request, id):
        if len(id) > 15:
            return Response({"ERROR": "Variable ID exceeds maximum length."}, status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)
    
        variables = Variables.objects.filter(id__iexact=id).first()
        if variables:
            return Response(VariableSerializer(variables, context={"embed": embed_fields}).data, status=status.HTTP_200_OK) 
        else:
            return Response({"ERROR": "Variable ID does not exist"}, status=status.HTTP_404_NOT_FOUND)

class API_Values(APIView):
    ALLOWED_EMBEDS = {"variable"}
    def get(self, request, id):
        if len(id) > 15:
            return Response({"ERROR": "Value ID exceeds maximum length."}, status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        value = VariableValues.objects.filter(value__iexact=id).first()
        if value:
            return Response(ValueSerializer(value, context={"embed": embed_fields}).data, status=status.HTTP_200_OK)
        else:
            return Response({"ERROR": "Value ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
class API_Levels(APIView):
    ALLOWED_EMBEDS = {"game"}
    def get(self, request, id):
        if len(id) > 15:
            return Response({"ERROR": "Level ID exceeds maximum length."}, status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed", "").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"}, status=status.HTTP_400_BAD_REQUEST)
    
        levels = Levels.objects.filter(id__iexact=id).first()
        if levels:
            return Response(LevelSerializer(levels, context={"embed": embed_fields}).data, status=status.HTTP_200_OK) 
        else:
            return Response({"ERROR": "Level ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
class API_Streams(APIView):
    def get(self,request):
        return Response(StreamSerializer(NowStreaming.objects.all(),many=True).data, status=status.HTTP_200_OK)
    
    def post(self,request):
        serializer = StreamSerializerPost(data=request.data)

        if not NowStreaming.objects.filter(Q(streamer__name__iexact=request.data["streamer"]) | Q(streamer__id__iexact=request.data["streamer"])).exists():
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"ERROR": "Stream from this player already exists."}, status=status.HTTP_409_CONFLICT)
    
    def put(self,request):
        stream = NowStreaming.objects\
                .filter(Q(streamer__name__iexact=request.data["streamer"])\
                | Q(streamer__id__iexact=request.data["streamer"])\
                | Q(streamer__twitch__icontains=request.data["streamer"])).first()
        
        serializer = StreamSerializerPost(instance=stream,data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=(status.HTTP_202_ACCEPTED if stream else status.HTTP_201_CREATED))
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        stream = NowStreaming.objects\
                .filter(Q(streamer__name__iexact=request.data["streamer"]) \
                | Q(streamer__id__iexact=request.data["streamer"]) \
                | Q(streamer__twitch__icontains=request.data["streamer"])).first()

        if stream:
            stream.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({"ERROR":"request.data['streamer'] is not in the model."}, status=status.HTTP_400_BAD_REQUEST)