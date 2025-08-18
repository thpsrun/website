from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Levels

from api.serializers.core import LevelSerializer


class API_Levels(APIView):
    """Viewset for viewing a specific level and its metadta.

    This viewset provides level metadata, including any embeds passed into the query.

    Methods:
        get:
            Returns level information based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Levels`

    Allowed Embeds:
        - `game`: Embeds the game associated with the category into the response.

    Embed Example:
        `/levels/123456?embed=game`

    Example Response (JSON):
        ```
        {
            "id": "29vkxe3d",
            "name": "Slam City Jam",
            "url": "https://www.speedrun.com/thug1/Slam_City_Jam"
        }
        ```
    """

    ALLOWED_EMBEDS = {"game"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a single level based on its ID.

        Parameters:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID of the level to be returned.

        Returns:
            Response: A response object containing the JSON data of a level.
        """
        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        levels = Levels.objects.filter(id__iexact=id).first()

        if levels:
            return Response(
                LevelSerializer(levels, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Level ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
