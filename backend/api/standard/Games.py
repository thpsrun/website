from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Categories, Games

from api.serializers.core import CategorySerializer, GameSerializer


class API_Games(APIView):
    """Viewset for viewing a specific game or all games.

    This viewset provides game information, including any embeds passed into the query.

    Methods:
        get:
            Returns game information based on a game ID or slug, or all games if "all" is used.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Games`

    Allowed Embeds:
        - `categories`: Embeds all categories associated with the game into the response.
        - `levels`: Embeds all levels associated with the game into the response.
        - `platforms`: Embeds all supported platforms for the game into the response.

    Embed Example:
        `/games/thps4?embed=categories,platforms`
        `/games/all?embed=categories,levels,platforms`

    Example Response (JSON):
        ```
        {
            "id": "n2680o1p",
            "name": "Tony Hawk's Underground",
            "slug": "thug1",
            "release": "2003-10-28",
            "boxart": "https://www.speedrun.com/static/game/n2680o1p/cover?v=16c7cc8",
            "twitch": "Tony Hawk's Underground",
            "defaulttime": "ingame",
            "idefaulttime": "ingame",
            "pointsmax": 1000,
            "ipointsmax": 100
        }
        ```
    """

    ALLOWED_EMBEDS = {"categories", "levels", "platforms"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a specific game's metadata based on its ID.

        If a game ID or slug is provided, returns that specific game's details. "All" can also be
        used to return a list for all games.Results can include embedded data using the `embed`
        query parameter.

        Args:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID of the game to be returned, or

        Returns:
            Response: A response object containing the JSON data of a game.
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

        if id == "all":
            games = Games.objects.all().order_by("release")
            return Response(
                GameSerializer(games, many=True, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )

        game = (
            Games.objects.filter(id__iexact=id).first()
            or Games.objects.filter(slug__iexact=id).first()
        )

        if game:
            return Response(
                GameSerializer(game, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Game ID or slug/abbreviation does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )


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
