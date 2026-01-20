import os
import time

import requests
from celery import shared_task
from django.db import transaction

from srl.m_tasks import src_api
from srl.models import Players
from srl.srcom.schema.src import SrcPlayersModel


@shared_task
def sync_players(
    players_data: str | dict,
    download_pfp: bool = False,
) -> None:
    """Creates or updates a `Players` model object based on the `players_data` argument.

    Arguments:
        players_data (str | dict): Either the unique ID (str) of the player or the embedded
            player dict information.
    """
    if isinstance(players_data, str):
        src_data: dict[dict, str] = src_api(
            f"https://speedrun.com/api/v1/users/{players_data}"
        )

        src_player = SrcPlayersModel.model_validate(src_data)
    else:
        src_player = SrcPlayersModel.model_validate(players_data)

    if src_player.pfp is not None and download_pfp:
        response = requests.get(src_player.pfp)

        while response.status_code == 420 or response.status_code == 503:
            time.sleep(60)
            response = requests.get(src_player.pfp)

        folder_path = "srl/static/pfp"
        os.makedirs(folder_path, exist_ok=True)

        file_name = f"{src_player.id}.jpg"
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, "wb") as f:
            f.write(response.content)
    else:
        file_path = None

    with transaction.atomic():
        Players.objects.update_or_create(
            id=src_player.id,
            defaults={
                "name": src_player.names.international,
                "url": src_player.weblink,
                "pfp": file_path if download_pfp else None,
                "pronouns": src_player.pronouns,
                "twitch": src_player.twitch_url,
                "youtube": src_player.youtube_url,
            },
        )
