from datetime import datetime

import requests
from celery import shared_task

from .m_tasks import src_api
from .models import Games


@shared_task
def test_ping():
    print(f"Ping! This is a test! {datetime.utcnow()}")


@shared_task
def src_check():
    headers = {}
    games = Games.objects.all()

    for game in games:
        newruns = src_api(
            f"https://speedrun.com/api/v1/runs?status=new&game={game['id']}"
        )

        if len(newruns) > 0:
            for run in newruns:
                requests.post(
                    f"http://localhost:8001/api/runs/{run['id']}", headers=headers
                )
