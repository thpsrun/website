from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import NowStreaming

from api.serializers.core import StreamSerializer, StreamSerializerPost


class API_Streams(APIView):
    """Viewset for viewing, creating, editing, or deleting a user's livestream status.

    This viewset provides the standard actions for creating, editing, or viewing a user's livestream
    status.

    Methods:
        get:
            Returns all currently available livestreams (no ID provided).
        post:
            Creates a new livestream entry after it passes validation.
        put:
            Updates (or creates) a new livestream entry after it passes validation.
        delete:
            Removes a livestream entry completely.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `NowStreaming`

    Example Response (JSON):
        ```
        [
            {
                "streamer": {
                    "player": "TH126",
                    "twitch": "https://www.twitch.tv/TH126",
                    "youtube": "https://www.youtube.com/user/TH126"
                },
                "game": {
                    "id": "w6jgk3x6",
                    "name": "Tony Hawk's Pro Skater 3+4",
                    "twitch": "Tony Hawk's Pro Skater 3+4"
                },
                "title": "THPS3+4 Speedruns for World Record",
                "offline_ct": 1,
                "stream_time": "2025-04-17T18:00:00Z"
            }
        ]
        ```
    """

    def get(
        self,
        _,
    ) -> JsonResponse:
        """Returns a list of all available streams currently in the database."""
        return Response(
            StreamSerializer(NowStreaming.objects.all(), many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request: HttpRequest,
    ) -> JsonResponse:
        """Creates a new livestream object.

        Args:
            request (HttpRequest): JSON information that must pass validation before being added.
        """
        serializer = StreamSerializerPost(data=request.data)

        streamcheck = NowStreaming.objects.filter(
            Q(streamer__name__iexact=request.data["streamer"])
            | Q(streamer__id__iexact=request.data["streamer"])
        ).exists()

        if not streamcheck:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"ERROR": "Stream from this player already exists."},
                status=status.HTTP_409_CONFLICT,
            )

    def put(
        self,
        request: HttpRequest,
    ) -> JsonResponse:
        """Updates (or creates) a livestream object.

        Args:
            request (HttpRequest): JSON information that must pass validation before being added.
        """
        stream = NowStreaming.objects.filter(
            Q(streamer__name__iexact=request.data["streamer"])
            | Q(streamer__id__iexact=request.data["streamer"])
            | Q(streamer__twitch__icontains=request.data["streamer"])
        ).first()

        serializer = StreamSerializerPost(instance=stream, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=(
                    status.HTTP_202_ACCEPTED if stream else status.HTTP_201_CREATED
                ),
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(
        self,
        request: HttpRequest,
    ) -> JsonResponse:
        """Removes a livestream object.

        Args:
            request (HttpRequest): JSON information that must pass validation before being deleted.
        """
        stream = NowStreaming.objects.filter(
            Q(streamer__name__iexact=request.data["streamer"])
            | Q(streamer__id__iexact=request.data["streamer"])
            | Q(streamer__twitch__icontains=request.data["streamer"])
        ).first()

        if stream:
            stream.delete()
            return Response("ok", status=status.HTTP_200_OK)
        else:
            return Response(
                {"ERROR": f"{request.data['streamer']} is not in the model."},
                status=status.HTTP_400_BAD_REQUEST,
            )
