import asyncio
import time

from django.shortcuts import redirect
from django.views.generic import ListView, View

from .init_series import init_series
from .tasks import import_obsolete, update_game, update_game_runs, update_player


class UpdateSeriesView(View):
    """Initalizes the Series and begins gathering data on all speedruns within it from SRC's API."""
    def get(self, request):
        series_ids = request.GET.getlist("series_ids")
        for series_id in series_ids:
            asyncio.run(init_series(series_id))

        return redirect("/illiad/srl/games/")


class UpdateGameView(ListView):
    """Updates all selected games, their metadata, categories, and variables from SRC's API."""
    def get(self, request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game.delay(game_id)

        return redirect("/illiad/srl/games/")


class RefreshGameRunsView(ListView):
    """Removes all games associated with the selected games to 'refresh' the leaderboard."""
    def get(self, request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game_runs.delay(game_id, 1)

        return redirect("/illiad/srl/games/")


class UpdateGameRunsView(ListView):
    """Updates all selected games, their metadata, categories, and variables from SRC's API."""
    def get(self, request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game_runs.delay(game_id, 0)

        return redirect("/illiad/srl/games/")


class UpdatePlayerView(ListView):
    """Updates all selected players and their metadata from SRC's API."""
    def get(self, request):
        player_ids = self.request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            update_player.delay(player)

        return redirect("/illiad/srl/players/")


class ImportObsoleteView(ListView):
    """Crawls all selected users to discover all speedruns within the Series to import obsolete."""
    def get(self, request):
        player_ids = self.request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            import_obsolete.delay(player, False)
            print("Speedrun.com is fucking with me... Waiting 10 extra seconds...")
            time.sleep(10)

        return redirect("/illiad/srl/players/")
