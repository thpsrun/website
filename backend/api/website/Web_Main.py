from typing import Any, List

from django.db.models.functions import TruncDate
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Runs

from api.serializers.core import GameSerializer, PlayerSerializer, RunSerializer
from api.website.permissions import ReadOnlyOrAuthenticated


class API_Web_Main(APIView):
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

    def _get_latest_wrs(
        self,
        embed_fields: list[str],
    ) -> list[dict[str, Any]]:
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

    def _get_latest_pbs(
        self,
        embed_fields: list[str],
    ) -> list[dict[str, Any]]:
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

    def _get_records(
        self,
        _,
    ) -> list[dict[str, Any]]:
        """Get grouped world records for main categories."""

        runs: List[Runs] = list(
            Runs.objects.exclude(vid_status__in=["new", "rejected"], obsolete=True)
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
            .filter(
                runtype="main",
                place=1,
                category__appear_on_main=True,
            )
            .order_by("-subcategory")
            .annotate(o_date=TruncDate("date"))
        )

        best_runs = {}

        for run in runs:
            if run.game.defaulttime == "realtime":
                time_val = run.time_secs
            elif run.game.defaulttime == "realtime_noloads":
                time_val = run.timenl_secs
            else:
                time_val = run.timeigt_secs

            key = (run.game.id, run.category.id)

            if key not in best_runs or time_val < best_runs[key][0]:
                best_runs[key] = (time_val, run)

        runs_list: list[Runs] = [r[1] for r in best_runs.values()]

        # Group runs together within the same game and subcategory for ties
        grouped_runs: list[dict] = []
        seen_records: set[tuple[str, str, float]] = set()

        for run in runs_list:
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

        run_list = sorted(grouped_runs, key=lambda x: x["game"].release)

        for run in run_list:
            if run["game"]:
                run["game"] = GameSerializer(run["game"]).data

        return run_list

    def get(
        self,
        request: HttpRequest,
    ) -> JsonResponse:
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
                    "ERROR": "Allowed queries: status, latest, latest-wrs, latest-pbs, records)."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
