from typing import List

from django.db.models import Exists, OuterRef, Prefetch
from django.db.models.functions import TruncDate
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Categories, Games, Runs, RunVariableValues, Variables

from api.serializers import (
    CategorySerializer,
    GameSerializer,
    PlayerSerializer,
    RunSerializer,
)


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


class API_Website_Categories(APIView):
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


class API_Website_Category_Runs(APIView):
    """Viewset for dynamically look up runs, depending on the categories, variables, or values given

    This viewset gives information about a category's runs. If not `subcat` query is given, then it
    will show ALL runs in that category. Using `?subcat=var123-val123` with a comma-separtion will
    allow you to more precisely select the runs wanted.

    Methods:
        get:
            Returns all runs in category, depending on the queries given.

    Permissions:
        - `ReadOnlyOrAuthenticated`: GET requests are public.

    Model: `Runs`
    """

    def get(
        self,
        request: HttpRequest,
        id: str,
    ) -> JsonResponse:
        subcats_raw = request.GET.get("subcats", "").split(",")
        subcats_raw = [item.strip() for item in subcats_raw if item.strip()]

        subcats = []
        for pair in subcats_raw:
            if "-" in pair:
                var_id, val_id = pair.split("-", 1)
                subcats.append((var_id, val_id))
            else:
                subcats.append((pair, None))

        runs_all = (
            Runs.objects.exclude(
                vid_status__in=["new", "rejected"],
                place=0,
            )
            .select_related(
                "game",
                "category",
                "player",
                "player__countrycode",
                "player2",
                "player2__countrycode",
            )
            .defer(
                "variables",
                "platform",
                "description",
            )
            .filter(category=id, obsolete=False)
        )

        if subcats:
            for var_id, val_id in subcats:
                runs_all = runs_all.filter(
                    Exists(
                        RunVariableValues.objects.filter(
                            run=OuterRef("pk"),
                            variable=var_id,
                            value=val_id,
                        )
                    )
                )

        runs_all: List[Runs] = list(runs_all)

        if runs_all:
            run_check = runs_all[0]
            run_type = run_check.runtype
            if run_type == "il":
                game_method = run_check.game.idefaulttime
            else:
                game_method = run_check.game.defaulttime

            timing_methods = {
                "realtime": "time_secs",
                "realtime_noloads": "timenl_secs",
                "ingame": "timeigt_secs",
            }

            order_field = timing_methods.get(game_method)
            runs_all.sort(key=lambda run: getattr(run, order_field))

            return Response(
                RunSerializer(runs_all, many=True).data, status=status.HTTP_200_OK
            )

        return Response(
            {"ERROR": "No runs could be returned."},
            status=status.HTTP_400_BAD_REQUEST,
        )
