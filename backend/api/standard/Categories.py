from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Categories

from api.serializers.core import CategorySerializer


class API_Categories(APIView):
    """Viewset for viewing a specific category.

    This viewset returns information on a single category, including any embeds passed into the
    query.

    Methods:
        get:
            Returns category information based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Categories`

    Allowed Embeds:
        - `game`: Embeds the game associated with the category into the response.
        - `variables`: Embeds all variables related to the category into the response.
        - `values`: Embeds all variables related to the category and its associated values into
        the response. NOTE: This takesp precedence over `variables`.

    Embed Example:
        `/categories/123456?embed=variables`

    Example Response (JSON):
        ```
        {
            "id": "rklge08d",
            "name": "Any%",
            "type": "per-game",
            "url": "https://www.speedrun.com/thps4#Any",
            "hidden": false
        }
        ```
    """

    ALLOWED_EMBEDS = {"game", "variables", "values"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a single category and its metadata based on its ID.

        Parameters:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID of the category to be returned.

        Returns:
            Response: A response object containing the JSON data of a category.
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

        category = Categories.objects.filter(id__iexact=id).first()
        if category:
            return Response(
                CategorySerializer(category, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Category ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
