"""
######################################################################################################################################################
### File Name: init_series.py
### Author: ThePackle
### Description: Script that kicks off discovery for a Series, its games, all of its variables, runs, etc.
                 This script is also dangerous - all data will be removed from the Models written below, then rewritten.
### Dependencies: srl/tasks, srl/models
######################################################################################################################################################
"""

from .tasks import src_api,update_game,update_category,update_level,update_variable,update_category_runs,update_platform
from .models import GameOverview, Categories, Levels, Variables, VariableValues,MainRuns,ILRuns,Players,NewRuns,NewWRs

def init_series(series_id):
    GameOverview.objects.all().delete()
    Categories.objects.all().delete()
    Levels.objects.all().delete()
    Variables.objects.all().delete()
    VariableValues.objects.all().delete()
    MainRuns.objects.all().delete()
    ILRuns.objects.all().delete()
    Players.objects.all().delete()
    #NewRuns.objects.all().delete()
    #NewWRs.objects.all().delete()

    src_games = src_api(f"https://www.speedrun.com/api/v1/series/{series_id}/games?max=50")

    if not isinstance(src_games,int):
        for game in src_games:
            game_check = src_api(f"https://www.speedrun.com/api/v1/games/{game['id']}?embed=platforms,levels,categories,variables")

            if not isinstance(game_check,int):
                print("CHECKING: " + game_check["names"]["international"])

                for plat in game_check["platforms"]["data"]:
                    update_platform(plat)

                update_game(game_check)

                for category in game_check["categories"]["data"]:
                    update_category(category,game["id"])

                if len(game_check["levels"]["data"]) > 0:
                    for level in game_check["levels"]["data"]:
                        update_level(level,game["id"])

                if len(game_check["variables"]["data"]) > 0:
                    for variable in game_check["variables"]["data"]:
                        update_variable(game['id'],variable)

                for category in game_check["categories"]["data"]:
                    update_category_runs(game_check["id"],category,game_check["levels"]["data"])

async def init_series_async(series_id):
    init_series(series_id)