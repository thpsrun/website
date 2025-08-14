from django.db.models import Q
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Runs

from api.serializers import GameSerializer, RunSerializer


class ReadOnlyOrAuthenticated(BasePermission):
    """
    Custom permission to only allow read access without authentication,
    but require authentication for write operations.
    """

    def has_permission(self, request: HttpRequest, _):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user and request.user.is_authenticated


class API_Website_Main(APIView):
    """Viewset for seeing information on the main page.

    This viewset provides standard information about

    Methods:
        get:
            Standard return used for the `/website/mainpage` endpoint.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public.

    Model: `Runs`

    Allowed Queries:
        - `latest-wrs`: Returns the 5 latest world records.
        - `latest-pbs`: Returns the 5 latest personal bests (excluding recent world records).
        - `records`: Returns the current world records for pre-defined/hard-coded categories.

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

    ALLOWED_QUERIES = {
        "latest-wrs",
        "latest-pbs",
        "records",
    }
    ALLOWED_EMBEDS = {
        "category",
        "level",
        "game",
        "variables",
        "platform",
        "players",
        "record",
    }
    permission_classes = [ReadOnlyOrAuthenticated]

    def _get_latest_wrs(self, embed_fields):
        """Get latest world records for latest-wrs query."""
        wrs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(place=1, obsolete=False, v_date__isnull=False)
            .order_by("-v_date")
        )[:5]

        return RunSerializer(wrs, many=True, context={"embed": embed_fields}).data

    def _get_latest_pbs(self, embed_fields):
        """Get latest personal bests for latest-pbs query."""
        pbs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"])
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(place__gt=1, obsolete=False, v_date__isnull=False)
            .order_by("-v_date")
        )[:5]

        return RunSerializer(pbs, many=True, context={"embed": embed_fields}).data

    def _get_records(self, _):
        """Get grouped world records for main categories."""
        subcategories = [
            "Any%",
            "Any% (6th Gen)",
            "100%",
            "Any% (No Major Glitches)",
            "All Goals & Golds (No Major Glitches)",
            "All Goals & Golds (All Careers)",
            "All Goals & Golds (6th Gen)",
            "Any% (6th Gen, Normal)",
            "100% (Normal)",
            "Any% (Beginner)",
            "100% (NSR)",
            "Story (Easy, NG+)",
            "100% (NG)",
            "Classic (Normal, NG+)",
            "Story Mode (Easy, NG+)",
            "Classic Mode (Normal)",
            "Any% (360/PS3)",
            "100% (360/PS3)",
            "Any% Tour Mode (All Tours, New Game)",
            "All Goals & Golds (All Tours, New Game)",
        ]

        exempt_games = [
            "GBA",
            "PSP",
            "GBC",
            "Category Extensions",
            "Remix",
            "Sk8land",
            "HD",
            "2x",
        ]

        exclusion_filter = Q()
        for game in exempt_games:
            exclusion_filter |= Q(game__name__icontains=game)

        runs = (
            Runs.objects.exclude(vid_status__in=["new", "rejected"], obsolete=True)
            .exclude(exclusion_filter)
            .select_related(
                "game",
                "player",
                "player__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(runtype="main", place=1, subcategory__in=subcategories)
            .order_by("-subcategory")
            .annotate(o_date=TruncDate("date"))
        )

        # Group runs together within the same game and subcategory for ties
        grouped_runs = []
        seen_records = set()

        for run in runs:
            key = (run.game.slug, run.subcategory, run.time)
            if key not in seen_records:
                grouped_runs.append(
                    {
                        "game": run.game,
                        "subcategory": run.subcategory,
                        "time": run.time,
                        "players": [],
                    }
                )
                seen_records.add(key)

            for record in grouped_runs:
                if (
                    record["game"].slug == run.game.slug
                    and record["subcategory"] == run.subcategory
                    and record["time"] == run.time
                ):
                    from api.serializers import PlayerSerializer

                    record["players"].append(
                        {
                            "player": (
                                PlayerSerializer(run.player).data
                                if run.player
                                else None
                            ),
                            "url": run.url,
                            "date": run.o_date,
                        }
                    )

        # Sort runs by game release date, oldest first
        run_list = sorted(grouped_runs, key=lambda x: x["game"].release, reverse=False)

        # Serialize game objects
        for run in run_list:
            if run["game"]:
                run["game"] = GameSerializer(run["game"]).data

        return run_list

    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        """Returns a speedrun based on its ID.

        Args:
            request (Request): The request object containing the information, queries, or embeds.

        Returns:
            Response: A response object containing the JSON data for the main page.
        """
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

        response_data = {}

        if "latest-wrs" in query_fields:
            response_data["latest_wrs"] = self._get_latest_wrs(embed_fields)

        if "latest-pbs" in query_fields:
            response_data["latest_pbs"] = self._get_latest_pbs(embed_fields)

        if "records" in query_fields:
            response_data["records"] = self._get_records(embed_fields)

        if response_data:
            return Response(response_data)
        else:
            return Response(
                {
                    "ERROR": "'all' can only be used with a query (status, latest, latest-wrs,\
                        latest-pbs, records)."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
