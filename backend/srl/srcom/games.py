from celery import shared_task
from django.db import transaction

from srl.m_tasks import src_api
from srl.models import Games
from srl.srcom.schema.src import SrcGamesModel


@shared_task
def sync_game(
    game_id: str,
) -> None:
    """Creates or updates a `Games` model object based on the `game_id` argument.

    Arguments:
        game_id (str): Unique ID for an SRC game.
    """
    src_data: dict[dict, str] = src_api(
        f"https://speedrun.com/api/v1/games/{game_id}?embed=platforms"
    )

    src_game = SrcGamesModel.model_validate(src_data)

    points_max = (
        1000
        if "category extensions" not in src_game.names.international.lower()
        else 50
    )

    ipoints_max = (
        200 if "category extensions" not in src_game.names.international.lower() else 50
    )

    with transaction.atomic():
        game, _ = Games.objects.update_or_create(
            id=src_game.id,
            defaults={
                "name": src_game.names.international,
                "slug": src_game.abbreviation,
                "release": src_game.release_date,
                "defaulttime": src_game.ruleset.defaulttime,
                "boxart": src_game.assets.cover_large.uri,
                "twitch": src_game.names.twitch,
                "pointsmax": points_max,
                "ipointsmax": ipoints_max,
            },
        )

        for plat in game.platforms:
            game.platforms.add(plat)
