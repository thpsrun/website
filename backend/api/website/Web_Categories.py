from django.db.models import Prefetch
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Categories, Games, Variables

from api.serializers.core import CategorySerializer
from api.website.permissions import ReadOnlyOrAuthenticated


class API_Web_Categories(APIView):
    """Viewset for dynamically looking up categories related to a game.

    This viewset provides standard information about all of the categories for a game, their
    associated `Variables` and then their associated `VariableValues`.

    Methods:
        get:
            Returns category information based on its ID.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public.

    Model: `Categories`, `Variables`, `VariableValues`
    """

    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        _: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a single game's categories, variables, and associated values.

        Parameters:
            id (str): The exact game ID to have its categories and variables returned.

        Allowed Embeds:
            - `variables`: Embeds all variables related to the category into the response.

        Returns:
            Response: A response object containing the JSON data of a game's categories.
        """
        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        game = Games.objects.filter(id__iexact=id).first()
        if not game:
            return Response(
                {"ERROR": "game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        categories = Categories.objects.filter(game=game).prefetch_related(
            Prefetch(
                "variables_set",
                queryset=Variables.objects.prefetch_related("variablevalues_set"),
            )
        )

        serializer = CategorySerializer(
            categories,
            many=True,
            context={"embed": ["variables", "values"]},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
