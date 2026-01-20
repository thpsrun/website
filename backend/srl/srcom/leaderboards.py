from celery import shared_task
from django.db import transaction

from srl.m_tasks import points_formula, src_api, time_conversion
from srl.models import Categories, Games, Runs
from srl.srcom.schema.src import SrcRunsModel


@shared_task
def sync_runs(
    runs_data: str | dict,
) -> None:
    """Creates or updates a `Runs` model object based on the `runs_data` argument.

    Arguments:
        runs_data (str | dict): Either the unique ID (str) of the player or the embedded
            player dict information.
    """
    if isinstance(runs_data, str):
        src_data: dict[dict, str] = src_api(
            f"https://speedrun.com/api/v1/runs/{runs_data}"
        )

        src_run = SrcRunsModel.model_validate(src_data)
    else:
        src_run = SrcRunsModel.model_validate(runs_data)

    run_date = src_run.submitted if src_run.submitted else src_run.date

    c_rta, c_nl, c_igt = time_conversion(src_run.times)

    get_game = Games.objects.only(
        "id",
        "name",
        "pointsmax",
        "ipointsmax",
        "defaulttime",
        "idefaulttime",
    ).get(id=src_run.game)

    if src_run.level is not None:
        wr_points = get_game.ipointsmax
        defaulttime = get_game.idefaulttime
    else:
        wr_points = get_game.pointsmax
        defaulttime = get_game.defaulttime
    ## Need to re-write logic to check for the placement of the run
    ## Need to figure out a lot of the logic.
    points = points_formula()

    default = {
        "runtype": "main",
        "game": src_run.game,
        "category": Categories.objects.only("id").get(id=src_run.category),
        "date": run_date,
        "v_date": src_run.status.verify_date,
        "time": c_rta,
        "time_secs": src_run.times.realtime_t,
        "timenl": c_nl,
        "timenl_secs": src_run.times.realtime_noloads_t,
        "timeigt": c_igt,
        "timeigt_secs": src_run.times.ingame_t,
        "points": points,
    }

    with transaction.atomic():
        Runs.objects.update_or_create()
