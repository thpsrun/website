"""
######################################################################################################################################################
### File Name: srl/views.py
### Author: ThePackle
### Description: Views that are loaded upon someone going to a specific webpage.
### Dependencies: srl/tasks.py, srl/init_series.py
######################################################################################################################################################
"""

import asyncio
from django.views.generic import ListView,View
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .tasks import update_game,update_game_runs,update_player,import_obsolete,import_srltimes
from .init_series import init_series

@method_decorator(csrf_exempt, name="dispatch")
class UpdateSeriesView(View):
    def get(self, request):
        series_ids = request.GET.getlist("series_ids")
        for series_id in series_ids:
            asyncio.run(init_series(series_id))

        return redirect("/admin/srl/gameoverview/")
    
class UpdateGameView(ListView):
    def get(self,request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game.delay(game_id)
            
        return redirect("/admin/srl/gameoverview/")
    
class RefreshGameRunsView(ListView):
    def get(self,request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game_runs.delay(game_id,1)
        
        return redirect("/admin/srl/gameoverview/")

class UpdateGameRunsView(ListView):
    def get(self,request):
        game_ids = self.request.GET.get("game_ids", "").split(",")
        for game_id in game_ids:
            update_game_runs.delay(game_id,0)
        
        return redirect("/admin/srl/gameoverview/")
    
class UpdatePlayerView(ListView):
    def get(self, request):
        player_ids = self.request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            update_player.delay(player)

        return redirect("/admin/srl/players/")
    
class ImportObsoleteView(ListView):
    def get(self, request):
        player_ids = self.request.GET.get("player_ids", "").split(",")
        for player in player_ids:
            #asyncio.run(import_obsolete(player))
            import_obsolete.delay(player)

        return redirect("/admin/srl/players/")

class ImportSRLTimes(ListView):
    def get(self, request):
        run_ids = self.request.GET.get("run_ids", "").split(",")
        
        for run in run_ids:
            asyncio.run(import_srltimes(run))
            
        
        return redirect("/admin/srl/")