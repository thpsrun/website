import asyncio

from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, View

from .init_series import init_series
from .tasks import import_obsolete, update_game, update_game_runs, update_player


@method_decorator(csrf_exempt, name="dispatch")
class UpdateSeriesView(View):
    def get(self, request):
        series_ids = request.GET.getlist("series_ids")
        for series_id in series_ids:
            asyncio.run(init_series(series_id))

        return redirect("/illiad/srl/games/")
    
class UpdateGameView(ListView):
    def get(self,request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game.delay(game_id)
            
        return redirect("/illiad/srl/games/")
    
class RefreshGameRunsView(ListView):
    def get(self,request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game_runs.delay(game_id,1)
        
        return redirect("/illiad/srl/games/")

class UpdateGameRunsView(ListView):
    def get(self,request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game_runs.delay(game_id,0)
        
        return redirect("/illiad/srl/games/")
    
class UpdatePlayerView(ListView):
    def get(self, request):
        player_ids = self.request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            update_player.delay(player)

        return redirect("/illiad/srl/players/")
    
class ImportObsoleteView(ListView):
    def get(self, request):
        player_ids = self.request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            import_obsolete.delay(player)

        return redirect("/illiad/srl/players/")