from celery import chain
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Runs

from api.serializers.core import RunSerializer
from api.tasks import normalize_src


class API_Runs(APIView):
    """Viewset for viewing, creating, or editing speedruns.

    This viewset provides the standard actions for creating, editing, or viewing speedruns,
    including any embeds passed into the query.

    Methods:
        get:
            Returns a speedrun based on its ID.
        post:
            Creates a new speedrun based upon the ID after it has been properly queried through
            the Speedrun.com API.
        put:
            Updates (or creates) a new speedrun based upon the ID after it has been properly
            queried through the Speedrun.com API.

    Permissions:
        - `IsAuthenticated`: Only authenticated users with a valid API key may use this endpoint.

    Model: `Runs`

    Allowed Queries:
        - `status`: Returns a list of speedruns awaiting verification (if the run has `new` as its
        `vid_status`).
            Example: `/runs/all?query=status`

    Embeds:
        - `category`: Embeds the related category into the response.
        - `level`: Embeds the related level into the response (only for individual-level speedruns).
        - `game`: Embeds the related game into the response.
        - `variables`: Embeds all related variables and values into the response.
        - `platform`: Embeds the related platform into the response.
        - `players`: Embeds all related players into the response.
        - `record`: Embeds world record information for the related category into the response.

    Embed Examples:
        - `/runs/123456?embed=category,level,game`
        - `/runs/123456?embed=players`

    Example Response (JSON):
        ```
        {
            "id": "z5l9eljy",
            "runtype": "main",
            "game": "xldeeed3",
            "category": "rklge08d",
            "level": null,
            "subcategory": "Any% (5th Gen)",
            "place": 1,
            "players": "68w4mqxg",
            "date": "2025-04-16T06:08:44Z",
            "times": {
                "defaulttime": "ingame",
                "time": "25m 42s",
                "time_secs": 1542.0,
                "timenl": "0",
                "timenl_secs": 0.0,
                "timeigt": "0",
                "timeigt_secs": 0.0
            },
            "record": z5l9eljy,
            "system": {
                "platform": "wxeod9rn",
                "emulated": true
            },
            "status": {
                "vid_status": "verified",
                "approver": "pj0v90mx",
                "v_date": "2025-04-16T22:09:46Z",
                "obsolete": false
            },
            "videos": {
                "video": "https://youtu.be/Xay5dWSfDQY",
                "arch_video": null
            },
            "variables": {
                "ylq9qkv8": "rqv4kprq"
            },
            "meta": {
                "points": 1000,
                "url": "https://www.speedrun.com/thps4/run/z5l9eljy"
            },
            "description": "this is a description"
        }
        ```
    """

    ALLOWED_QUERIES = {"status"}
    ALLOWED_EMBEDS = {
        "category",
        "level",
        "game",
        "variables",
        "platform",
        "players",
        "record",
    }

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        """Returns a speedrun based on its ID.

        Args:
            request (HttpRequest): The request object containing the information, queries, or embeds
            id (str): The exact ID of the speedrun requesting to be returned.
                - "all" is a valid `id`, but must be used in conjunction with a query.

        Returns:
            Response: A response object containing the JSON data of a speedrun.
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

        if invalid_queries:
            return Response(
                {"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},
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
            if "status" in query_fields:
                new_runs = Runs.objects.filter(vid_status="new")
                runs = RunSerializer(
                    new_runs, many=True, context={"embed": embed_fields}
                ).data

                return Response(
                    {
                        "new_runs": runs,
                    }
                )
            else:
                return Response(
                    {"ERROR": "'all' can only be used with a query (status)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            run = Runs.objects.filter(id__iexact=id).first()
            if run:
                return Response(
                    RunSerializer(run, context={"embed": embed_fields}).data,
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"ERROR": "run id provided does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

    def post(
        self,
        _,
        id: str,
    ) -> JsonResponse:
        """Creates a new speedrun object based on its ID.

        After the `id` is given, the data is normalized, processed, and validated before it is
        added as a new `Runs` model object.

        Args:
            id (str): The exact ID of the speedrun requesting to be added to the database.

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s_chain = chain(normalize_src.s(id))()
        normalize = s_chain.get()

        if normalize == "invalid":
            return Response(
                {"ERROR": "id provided does not belong to this leaderboard's games."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            run = Runs.objects.filter(id=id).first()
            if run:
                return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"ERROR": f"Unknown error - The run id {id} could not be called."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    def put(
        self,
        _,
        id,
    ) -> JsonResponse:
        """Updates (or creates) a speedrun object based on its ID.

        After the `id` is given, the data is normalized, processed, and validated before it is
        updated in the `Runs` model. If the `id` does not exist already, it is added.

        Args:
            id (str): The exact ID of the speedrun requesting to be updated or added to the database

        Returns:
            Response: A response object containing the JSON data of a speedrun.
        """

        if len(id) >= 15:
            return Response(
                {"ERROR": "id must be 15 characters or less."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        s_chain = chain(normalize_src.s(id))()
        normalize = s_chain.get()

        if normalize == "invalid":
            return Response(
                {"ERROR": "id provided does not belong to this leaderboard's games."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            run = Runs.objects.filter(id=id).first()
            if run:
                return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"ERROR": f"Unknown error - The run id {id} could not be called."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
