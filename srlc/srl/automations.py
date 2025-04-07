######################################################################################################################################################
### File Name: srl/automations.py
### Author: ThePackle
### Description: This is where different automations can be created, then you can use Django Celery Beats to set the schedule.
### Dependencies: srl/m_tasks, srl/models
######################################################################################################################################################
from celery import shared_task
from datetime import datetime
from .tasks import *
from .models import *
from .m_tasks import src_api
import requests

@shared_task
def test_ping():
    print(f"Ping! This is a test! {datetime.utcnow()}")

@shared_task
def src_check():

    games = GameOverview.objects.all()

    for game in games:
        newruns = src_api(f"https://speedrun.com/api/v1/runs?status=new&game={game['id']}")

        if len(newruns) > 0:
            for run in newruns:
                requests.post(f"http://localhost:8001/api/runs/{run['id']}",headers=headers)