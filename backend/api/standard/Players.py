from celery import chain
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Players
from srl.tasks import update_player

from api.serializers.core import (
    PlayerSerializer,
    PlayerSerializerPost,
    PlayerStreamSerializer,
)


class API_Players(APIView):
    """Viewset for viewing a specific player.

    This viewset provides the standard actions for viewing a specific player.

    Methods:
        get:
            Returns information on a player based on their username or ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Players`

    Allowed Queries:
        - `streamexceptions`: Returns a list of users who are marked as exempt and wishing to not
        appear on streams.
            Example: `/players/all?query=streamexceptions`

    Example Response (JSON):
        ```
        {
            "id": "e8ew5p80",
            "name": "ThePackle",
            "nickname": "Packle",
            "url": "https://www.speedrun.com/user/ThePackle",
            "pfp": "pfp_link",
            "country": "United States",
            "pronouns": "He/Him",
            "twitch": "https://www.twitch.tv/ThePackle",
            "youtube": "https://www.youtube.com/user/ThePackle",
            "twitter": null,
            "ex_stream": false,
            "awards": [
                {
                    "name": "Most Helpful (2022)"
                }
            ],
            "stats": {
                "total_pts": 16389,
                "main_pts": 15251,
                "il_pts": 1138,
                "total_runs": 50
            }
        }
        ```
    """

    ALLOWED_QUERIES = {"streams"}
    ALLOWED_EMBEDS = {"stats"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a specific player's information based on its ID.

        Args:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID or username of the player requesting to be returned.
                - "all" is a valid `id`, but must be used in conjunction with a query.

        Returns:
            Response: A response object containing the JSON data of a player.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_fields = request.GET.get("query", "").split(",")
        query_fields = [field.strip() for field in query_fields if field.strip()]
        invalid_queries = [
            field for field in query_fields if field not in self.ALLOWED_QUERIES
        ]

        embed_fields = request.GET.get("embed", "").split(",")
        embed_fields = [field.strip() for field in embed_fields if field.strip()]
        invalid_embeds = [
            field for field in embed_fields if field not in self.ALLOWED_EMBEDS
        ]

        if invalid_embeds:
            return Response(
                {"ERROR": f"Invalid embed(s): {', '.join(invalid_embeds)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invalid_queries:
            return Response(
                {"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if id == "all":
            if "streams" in query_fields:
                players = Players.objects.only(
                    "id", "name", "twitch", "youtube", "ex_stream"
                ).filter(Q(twitch__isnull=False) | Q(youtube__isnull=False))

                return Response(
                    PlayerStreamSerializer(players, many=True).data,
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"ERROR": "'all' can only be used with a query (streams)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        player = (
            Players.objects.filter(id__iexact=id).first()
            or Players.objects.filter(name__iexact=id).first()
        )

        if player:
            return Response(
                PlayerSerializer(player, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Player ID or Name does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Forces the `player` object to be updated from the Speedrun.com API.

        After the `id` is given, the player's data will be normalized and their player information
        will be properly updated in the `Players` model.

        Args:
            id (str): The exact ID or player name of the player being updated.

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) > 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        player = (
            Players.objects.only(
                "id",
                "name",
                "twitch",
                "youtube",
                "ex_stream",
            )
            .filter(
                Q(id__iexact=id) | Q(name__iexact=id),
            )
            .first()
        )

        if player:
            player_id = player.id

            if not request.data.get("ex_stream"):
                request.data.update({"ex_stream": player.ex_stream})

            if not request.data.get("nickname"):
                request.data.update({"nickname": player.nickname})

            serializer = PlayerSerializerPost(
                instance=player,
                data=request.data,
            )

            if serializer.is_valid():
                serializer.save()
                chain(update_player.s(player_id))()

                return Response(
                    serializer.data,
                    status=status.HTTP_202_ACCEPTED,
                )
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            try:
                chain(update_player.s(id))()

                return Response(
                    "ok",
                    status=status.HTTP_200_OK,
                )
            except AttributeError:
                return Response(
                    {"ERROR": "Player ID or name does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception:
                return Response(
                    {"ERROR": "An unknown error has occurred."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
