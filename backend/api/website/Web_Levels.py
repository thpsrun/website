from django.db.models import Case, Prefetch, Q, When
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Games, Levels, Variables

from api.ordering import get_ordered_level_names
from api.serializers.core import LevelSerializer
from api.website.permissions import ReadOnlyOrAuthenticated


class API_Web_Levels(APIView):
    """Viewset for looking up levels related to a game.

    This viewset provides standard information about all of the levels for a game.

    Methods:
        get:
            Returns level information based on its ID.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public.

    Model: `Games`, `Categories`, `Variables`, `VariableValues`
    """

    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        _: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a single game's categories, variables, and associated values.

        Parameters:
            id (str): The exact game ID or slug to have its categories and variables returned.

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

        game = Games.objects.filter(Q(id__iexact=id) | Q(slug__iexact=id)).first()
        if not game:
            return Response(
                {"ERROR": "game not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        get_order = get_ordered_level_names(game.slug)
        level_order = Case(
            *(When(name=name, then=position) for position, name in enumerate(get_order))
        )

        levels = (
            Levels.objects.filter(game=game)
            .prefetch_related(
                Prefetch(
                    "variables_set",
                    queryset=Variables.objects.prefetch_related("variablevalues_set"),
                )
            )
            .order_by(level_order)
        )

        serializer = LevelSerializer(
            levels,
            many=True,
            context={"embed": ["variables", "values"]},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
