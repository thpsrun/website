from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseBadRequest,HttpResponseNotFound
from .serializers import *
from srl.tasks import *
from api.tasks import *
from django.db.models import Count,F,Subquery,OuterRef, Q
from django.http import JsonResponse

class API_Runs(APIView):
    ALLOWED_QUERIES = {"status"}
    ALLOWED_EMBEDS  = {"category","level","game","platform","players"}
    def get(self,request,id):
        query_fields    = request.GET.get("query","").split(",")
        query_fields    = [field.strip() for field in query_fields if field.strip()] 
        invalid_queries = [field for field in query_fields if field not in self.ALLOWED_QUERIES]

        if invalid_queries:
            return Response({"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},status=status.HTTP_400_BAD_REQUEST)
        
        embed_fields   = request.GET.get("embed","").split(",")
        embed_fields   = [field.strip() for field in embed_fields if field.strip()] 
        invalid_embeds = [field for field in embed_fields if field not in self.ALLOWED_EMBEDS]

        if invalid_embeds:
            return Response({"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},status=status.HTTP_400_BAD_REQUEST)

        if id == "all":
            if "status" in query_fields:
                m_runs = Runs.objects.filter(vid_status="new")

                main_runs = RunSerializer(m_runs,many=True,context={"embed": embed_fields}).data
                
                return Response({
                    "main_runs" : main_runs,
                })
            else:
                return Response({"ERROR": "'all' can only be used with a query (status)."},status=status.HTTP_400_BAD_REQUEST)
        else:
            run = Runs.objects.filter(id__iexact=id).first()
            if run:
                return Response(RunSerializer(run,context={"embed": embed_fields}).data,status=status.HTTP_200_OK)
            else:
                return Response({"ERROR": "run id provided does not exist."},status=status.HTTP_200_OK)

    def post(self,request,id):
        if len(id) > 10:
            return Response({"ERROR": "id must be less than 10 characters."},status=status.HTTP_400_BAD_REQUEST)
        
        normalize = normalize_src.delay(id)
        ilcheck = normalize.get()
        time.sleep(1) ## Sometimes the other celery tasks are slow, so this will allow them to quickly finish before providing a response.

        if ilcheck == "invalid":
            return Response({"ERROR": "id provided does not belong to this leaderboard's games."},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(RunSerializer(Runs.objects.get(id=id)).data,status=status.HTTP_201_CREATED)
              
    def put(self,request,id):
        if len(id) > 10:
            return Response({"ERROR": "id must be less than 10 characters."},status=status.HTTP_400_BAD_REQUEST)
        
        normalize = normalize_src.delay(id)
        ilcheck = normalize.get()
        time.sleep(1) ## Sometimes the other celery tasks are slow, so this will allow them to quickly finish before providing a response.

        if ilcheck == "invalid":
            return Response({"ERROR": "id provided does not belong to this leaderboard's games."},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(RunSerializer(Runs.objects.get(id=id)).data,status=status.HTTP_201_CREATED)
    
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

            main_runs = Runs.objects.main().filter(player=player).filter(obsolete=False)
            il_runs   = Runs.objects.il().filter(player=player).filter(obsolete=False)

            main_data = RunSerializer(main_runs,many=True,context={"embed": embed_fields}).data
            il_data   = RunSerializer(il_runs,many=True,context={"embed": embed_fields}).data

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
            return Response(GameSerializer(games,many=True,context={"embed": embed_fields}).data,status=status.HTTP_200_OK)
        
        game = GameOverview.objects.filter(id__iexact=id).first() or GameOverview.objects.filter(abbr__iexact=id).first()
        if game:
            return Response(GameSerializer(game,context={"embed": embed_fields}).data,status=status.HTTP_200_OK)
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
            return Response(CategorySerializer(category,context={"embed": embed_fields}).data,status=status.HTTP_200_OK) 
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
            return Response(VariableSerializer(variables,context={"embed": embed_fields}).data,status=status.HTTP_200_OK) 
        else:
            return Response({"ERROR": "Variable ID does not exist"},status=status.HTTP_404_NOT_FOUND)

""" 
### Going to remove later, probably.
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
            }) """
            
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
            return Response(LevelSerializer(levels,context={"embed": embed_fields}).data,status=status.HTTP_200_OK) 
        else:
            return Response({"ERROR": "Level ID does not exist"},status=status.HTTP_404_NOT_FOUND)
        
class API_Streams(APIView):
    def get(self,request):
        return Response(StreamSerializer(NowStreaming.objects.all(),many=True).data,status=status.HTTP_200_OK)
    
    def post(self,request):
        serializer = StreamSerializerPost(data=request.data)

        if not NowStreaming.objects.filter(Q(streamer__name__iexact=request.data["streamer"]) | Q(streamer__id__iexact=request.data["streamer"])).exists():
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"ERROR": "Stream from this player already exists."},status=status.HTTP_409_CONFLICT)
    
    def put(self,request):
        stream = NowStreaming.objects.filter(Q(streamer__name__iexact=request.data["streamer"]) | Q(streamer__id__iexact=request.data["streamer"]) | Q(streamer__twitch__icontains=request.data["streamer"])).first()
        
        serializer = StreamSerializerPost(instance=stream,data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=(status.HTTP_202_ACCEPTED if stream else status.HTTP_201_CREATED))
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        stream = NowStreaming.objects.filter(Q(streamer__name__iexact=request.data["streamer"]) | Q(streamer__id__iexact=request.data["streamer"]) | Q(streamer__twitch__icontains=request.data["streamer"])).first()

        if stream:
            stream.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({"ERROR":f"request.data['streamer'] is not in the model."},status=status.HTTP_400_BAD_REQUEST)