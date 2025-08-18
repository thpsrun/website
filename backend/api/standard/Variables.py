from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Variables

from api.serializers.core import VariableSerializer


class API_Variables(APIView):
    """Viewset for viewing a specific variable.

    This viewset returns information on a single variable, including any embeds passed into the
    query.

    Methods:
        get:
            Returns variable information based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Variables`

    Allowed Embeds:
        - `game`: Embeds the game associated with the variable into the response.
        - `values`: Embeds all values available for the variable into the response.

    Example:
        `/variables/123456?embed=values`

    Example Response (JSON):
        ```
        {
            "id": "ylq9qkv8",
            "name": "Version",
            "cat": "rklge08d",
            "all_cats": false,
            "scope": "full-game",
            "hidden": false
        }
        ```
    """

    ALLOWED_EMBEDS = {"game", "values"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a single variable's metadata and values based on its ID.

        Parameters:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID of the variable to be returned.

        Returns:
            Response: A response object containing the JSON data of a variable.
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

        variables = Variables.objects.filter(id__iexact=id).first()
        if variables:
            return Response(
                VariableSerializer(variables, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Variable ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
