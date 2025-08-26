from .models import Players
from .tasks import (
    import_obsolete,
    src_api,
    update_category,
    update_category_runs,
    update_game,
    update_level,
    update_platform,
    update_variable,
)


def init_series(
    series_id: str,
) -> None:
    """Initializes the gathering of all data for the entire Series from the Speedrun.com API"""

    # Removes all objects from all of the listed models below.
    # Initialize Series should only be performed by the superadmin.
    # It also removes all objects in all models, then re-creates them.
    # If the following lines are commented, the removal won't happen.
    # If you want the removal to still occur, uncomment these lines.

    """Games.objects.all().delete()
    Categories.objects.all().delete()
    Levels.objects.all().delete()
    Variables.objects.all().delete()
    VariableValues.objects.all().delete()
    Runs.objects.all().delete()
    Players.objects.all().delete()
    MainRunTimeframe.objects.all().delete()"""

    # Iterates through the series ID provided to find all of the games associated.
    # Max is set to 50, but can be increased.
    src_games = src_api(f"https://speedrun.com/api/v1/series/{series_id}/games?max=50")

    if not isinstance(src_games, int):
        for game in src_games:
            game_check = src_api(
                f"https://speedrun.com/api/v1/games/"
                f"{game['id']}?embed=platforms,levels,categories,variables"
            )

            if not isinstance(game_check, int):
                for plat in game_check["platforms"]["data"]:
                    update_platform.delay(plat)

                update_game.delay(game["id"])

                for category in game_check["categories"]["data"]:
                    update_category.delay(
                        category,
                        game["id"],
                    )

                if len(game_check["levels"]["data"]) > 0:
                    for level in game_check["levels"]["data"]:
                        update_level.delay(
                            level,
                            game["id"],
                        )

                if len(game_check["variables"]["data"]) > 0:
                    for variable in game_check["variables"]["data"]:
                        update_variable.delay(
                            game["id"],
                            variable,
                        )

                for category in game_check["categories"]["data"]:
                    update_category_runs.delay(
                        game_check["id"],
                        category,
                        game_check["levels"]["data"],
                    )

    # Speedrun.com API sucks sometimes and will miss some runs; this reiterates to add runs it
    # somehow missed the first time. Good website.
    # This may take a while...
    redo = 0
    while redo < 2:
        for player in Players.objects.only("id").values_list("id", flat=True):
            import_obsolete.delay(player)

            redo = redo + 1


async def init_series_async(
    series_id: str,
) -> None:
    """Asynchronously starts the data collection from the Series."""
    # Actually kicks off the initialization of the code.
    # Kinda ass, should be fixed sometime. But, if it ain't broke...
    init_series(series_id)
