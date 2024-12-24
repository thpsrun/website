"""
######################################################################################################################################################
### File Name: init_series.py
### Author: ThePackle
### Description: Script that kicks off discovery for a Series, its games, all of its variables, runs, etc.
                 This script is also dangerous - all data will be removed from the Models written below, then rewritten.
### Dependencies: srl/tasks, srl/models
######################################################################################################################################################
"""

import asyncio
from .tasks import src_api,update_game,update_category,update_level,update_variable,update_category_runs,update_platform,import_obsolete
from .models import GameOverview,Categories,Levels,Variables,VariableValues,MainRuns,ILRuns,Players,NewRuns,NewWRs,MainRunTimeframe

def init_series(series_id):
    ## Removes all objects from all of the listed models below.
    ## Initialize Series should only be performed by the superadmin.
    ## If you want to re-enable this, just uncomment the lines.
    """GameOverview.objects.all().delete()
    Categories.objects.all().delete()
    Levels.objects.all().delete()
    Variables.objects.all().delete()
    VariableValues.objects.all().delete()
    MainRuns.objects.all().delete()
    ILRuns.objects.all().delete()
    Players.objects.all().delete()
    NewRuns.objects.all().delete()
    NewWRs.objects.all().delete()
    MainRunTimeframe.objects.all().delete()"""

    ## Iterates through the series ID provided to find all of the games associated. Max is set to 50, but can be increased.
    ## After all games are found, they are interated upon to add the platforms, runs, categories, and so on as seen below.
    ##
    ## This process can take some time, since we are relying upon SRL's API... which is hit or miss (mostly miss).
    
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
    
    ## Speedrun.com API sucks sometimes and will miss some runs; this reiterates to add runs it
    ## somehow missed the first time. Good website.
    ##
    ## This may take a while...
    redo = 0
    while redo < 3:
        for player in Players.objects.values_list("id", flat=True):
            print(f"IMPORTING {player} OBSOLETE RUNS...")
            asyncio.run(import_obsolete(player))
            
            redo = redo + 1

## Actually kicks off the initialization of the code.
## Kinda ass, should be fixed sometime. But, if it ain't broke...
async def init_series_async(series_id):
    init_series(series_id)