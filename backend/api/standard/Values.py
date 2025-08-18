from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import VariableValues

from api.serializers.core import ValueSerializer


class API_Values(APIView):
    """Viewset for viewing a specific value.

    This viewset returns a value's data, including any embeds passed into the query.

    Methods:
        get:
            Returns value info based on its ID.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `VariableValues`

    Allowed Embeds:
        - `variable`: Embeds the full variable metadata associated with this value into the
        response.

    Embed Example:
        `/values/123456?embed=variable`

    Example Response (JSON):
        ```
        {
            "value": "5lek6rml",
            "name": "6th Gen",
            "hidden": false,
            "variable": "ylq9qkv8"
        }
        ```
    """

    ALLOWED_EMBEDS = {"variable"}

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a single value's metadata and related variable based on its ID.

        Parameters:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID of the value to be returned.

        Returns:
            Response: A response object containing the JSON data of a value.
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

        value = VariableValues.objects.filter(value__iexact=id).first()

        if value:
            return Response(
                ValueSerializer(value, context={"embed": embed_fields}).data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"ERROR": "Value ID does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
