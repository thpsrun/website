from srl.srcom import (
    sync_categories,
    sync_game,
    sync_levels,
    sync_obsolete_runs,
    sync_platforms,
    sync_variables,
)
from srl.srcom.schema.src import SrcGamesModel

from .models import Players
from .tasks import src_api


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

    if isinstance(src_games, dict):
        for game in src_games:
            game_data = src_api(
                f"https://speedrun.com/api/v1/games/"
                f"{game['id']}?embed=platforms,levels,categories,variables"
            )

            game_data = SrcGamesModel.model_validate(game_data)

            if not isinstance(game_data, int):
                for platform in game_data.platforms:
                    sync_platforms.delay(platform.model_dump())

                sync_game.delay(game_data.id)

                if game_data.categories:
                    for category in game_data.categories:
                        sync_categories.delay(category.model_dump())

                if game_data.levels:
                    for level in game_data.levels:
                        sync_levels.delay(level.model_dump())

                if game_data.variables:
                    for variable in game_data.variables:
                        sync_variables.delay(variable.model_dump())

                # Add code for mass querying runs.

    # Speedrun.com API sucks sometimes and will miss some runs; this reiterates to add runs it
    # somehow missed the first time. Good website.
    # This may take a while...
    redo = 0
    while redo < 2:
        players = Players.objects.only("id").all()
        for player in players:
            sync_obsolete_runs(player.id)
            redo = redo + 1


async def init_series_async(
    series_id: str,
) -> None:
    """Asynchronously starts the data collection from the Series."""
    # Actually kicks off the initialization of the code.
    # Kinda ass, should be fixed sometime. But, if it ain't broke...
    init_series(series_id)
