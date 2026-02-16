import asyncio
from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, View

from srl.init_series import init_series
from srl.models import Categories, Games, Variables, VariableValues
from srl.srcom import sync_game, sync_game_runs, sync_obsolete_runs, sync_players


class UpdateSeriesView(View):
    """Initalizes the Series and begins gathering data on all speedruns within it from SRC's API."""

    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        series_ids = request.GET.getlist("series_ids")
        for series_id in series_ids:
            asyncio.run(init_series(series_id))

        return redirect("/illiad/srl/games/")


class UpdateGameView(ListView):
    """Updates all selected games, their metadata, categories, and variables from SRC's API."""

    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        game_ids = request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            sync_game.delay(game_id)

        return redirect("/illiad/srl/games/")


class RefreshGameRunsView(ListView):
    """Removes all games associated with the selected games to 'refresh' the leaderboard."""

    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        game_ids = request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            sync_game_runs.delay(game_id, 1)

        return redirect("/illiad/srl/games/")


class UpdateGameRunsView(ListView):
    """Updates all selected games, their metadata, categories, and variables from SRC's API."""

    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        game_ids = request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            sync_game_runs.delay(game_id, 0)

        return redirect("/illiad/srl/games/")


class UpdatePlayerView(ListView):
    """Updates all selected players and their metadata from SRC's API."""

    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        player_ids = request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            sync_players.delay(player)

        return redirect("/illiad/srl/players/")


class ImportObsoleteView(ListView):
    def get(
        self,
        request: HttpRequest,
    ) -> HttpResponse:
        player_ids = request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            sync_obsolete_runs(player)

        return redirect("/illiad/srl/players/")


class ManageMainVisibilityView(View):
    """Admin view to manage appear_on_main for categories and variable values per game."""

    def _build_context(
        self,
        game: Games,
    ) -> dict[str, Any]:
        """Build the tree of categories and their variable values for a game."""
        categories = (
            Categories.objects.filter(game=game)
            .order_by("name")
            .prefetch_related(
                "variables_set__variablevalues_set",
            )
        )

        categories_data: list[dict[str, Any]] = []
        for cat in categories:
            variable_values: list[dict[str, Any]] = []
            for var in cat.variables_set.all():  # type: ignore
                for vv in var.variablevalues_set.all():
                    variable_values.append(
                        {
                            "variable_name": var.name,
                            "value": vv,
                        }
                    )

            global_vars = Variables.objects.filter(
                game=game,
                cat__isnull=True,
                scope__in=["global", "full-game"],
            ).prefetch_related("variablevalues_set")

            for var in global_vars:
                for vv in var.variablevalues_set.all():  # type: ignore
                    if not any(
                        existing["value"].value == vv.value
                        for existing in variable_values
                    ):
                        variable_values.append(
                            {
                                "variable_name": f"{var.name} (global)",
                                "value": vv,
                            }
                        )

            categories_data.append(
                {
                    "category": cat,
                    "variable_values": variable_values,
                }
            )

        return {
            "game": game,
            "categories": categories_data,
            "title": f"Main Page Visibility: {game.name}",
            "opts": Games._meta,
            "has_view_permission": True,
        }

    def get(
        self,
        request: HttpRequest,
        game_id: str,
    ) -> HttpResponse:
        game = get_object_or_404(Games, id=game_id)
        context = self._build_context(game)
        return render(request, "admin/srl/manage_main_visibility.html", context)

    def post(
        self,
        request: HttpRequest,
        game_id: str,
    ) -> HttpResponse:
        game = get_object_or_404(Games, id=game_id)

        categories = Categories.objects.filter(game=game)
        for cat in categories:
            new_value = f"cat_{cat.id}" in request.POST
            if cat.appear_on_main != new_value:
                cat.appear_on_main = new_value
                cat.save(update_fields=["appear_on_main", "updated_at"])

        game_variable_values = VariableValues.objects.filter(
            var__game=game,
        )
        for vv in game_variable_values:
            new_value = f"vv_{vv.value}" in request.POST
            if vv.appear_on_main != new_value:
                vv.appear_on_main = new_value
                vv.save(update_fields=["appear_on_main", "updated_at"])

        messages.success(request, f"Main page visibility updated for {game.name}.")
        return redirect(
            request.path,
        )
