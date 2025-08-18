from typing import List

from django.db.models import Exists, OuterRef, Q
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from srl.models import Categories, Games, Runs, RunVariableValues, VariableValues

from api.serializers.core import RunSerializer
from api.website.permissions import ReadOnlyOrAuthenticated


class API_Web_Leaderboard(APIView):
    """Viewset for leaderboard lookup, depending on the categories, variables, or values given.

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

    ALLOWED_QUERIES = {"obsolete"}

    permission_classes = [ReadOnlyOrAuthenticated]

    def get(
        self,
        request: HttpRequest,
        gameid: str,
        catid: str,
        subcats: str | None = None,
    ) -> JsonResponse:
        subcat_list = subcats.rstrip("/").split("/") if subcats else []
        query_fields = request.GET.get("query", "").split(",")
        query_fields = [item.strip() for item in query_fields if item.strip()]

        invalid_queries = [
            field for field in query_fields if field not in self.ALLOWED_QUERIES
        ]

        if invalid_queries:
            return Response(
                {"ERROR": f"Invalid queries: {', '.join(invalid_queries)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        real_game = (
            Games.objects.only("id").filter(Q(id=gameid) | Q(slug=gameid)).first()
        )
        real_cat = (
            Categories.objects.only("id")
            .filter(game=real_game)
            .filter(Q(id=catid) | Q(slug=catid))
        ).first()

        runs_all: Runs = (
            Runs.objects.exclude(
                vid_status__in=["new", "rejected"],
            )
            .select_related(
                "game",
                "category",
                "platform",
                "player",
                "player__countrycode",
                "player2",
                "player2__countrycode",
            )
            .prefetch_related("variables")
            .filter(
                game=real_game,
                category=real_cat,
            )
        )

        if "obsolete" not in query_fields:
            runs_all = runs_all.filter(obsolete=False)

        if subcats:
            for val_id in subcat_list:
                # This sets up two separate queries to run. query is used as the primary, since it
                # is more often that a Variable has a category associated. If that returns nothing,
                # then the fallback query is used to see if the Variable is instead a "global" var.
                # If that also fails, then it most likely does not exist.
                real_value_query = real_value = VariableValues.objects.filter(
                    var__game=real_game
                ).filter(var__cat=real_cat)

                real_value_fallback = VariableValues.objects.filter(
                    var__game=real_game
                ).filter(var__all_cats=True)

                real_value = real_value_query.filter(
                    Q(value=val_id) | Q(slug=val_id)
                ).first()

                if not real_value:
                    real_value = real_value_fallback.filter(
                        Q(value=val_id) | Q(slug=val_id)
                    ).first()

                if real_value:
                    runs_all = runs_all.filter(
                        Exists(
                            RunVariableValues.objects.filter(run=OuterRef("pk")).filter(
                                value=real_value
                            )
                        )
                    )
                else:
                    return Response(
                        {"ERROR": f"Invalid path: {real_game}, {real_cat}, {val_id}"},
                        status=status.HTTP_400_BAD_REQUEST,
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
                RunSerializer(
                    runs_all,
                    context={"embed": "platform, players"},
                    many=True,
                ).data,
                status=status.HTTP_200_OK,
            )

        return Response(
            {"ERROR": "No runs could be returned."},
            status=status.HTTP_400_BAD_REQUEST,
        )
