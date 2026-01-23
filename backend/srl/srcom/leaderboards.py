from celery import shared_task
from django.db import transaction

from srl.m_tasks import points_formula, time_conversion
from srl.models import (
    Categories,
    Games,
    Levels,
    Platforms,
    Players,
    RunPlayers,
    Runs,
    RunVariableValues,
)
from srl.srcom.players import sync_players
from srl.srcom.schema.internal import RunSyncContext, RunSyncTimesContext
from srl.srcom.schema.src import SrcLeaderboardModel
from srl.srcom.utils import lrt_fix, update_obsolete, update_standings


@shared_task
def sync_leaderboards(
    leaderboard_data: dict,
) -> None:
    """Creates or updates a `Runs` model object based on the `runs_data` argument.

    Arguments:
        runs_data (str | dict): Either the unique ID (str) of the player or the embedded
            player dict information.
    """
    LRT_FIX = False

    src_lb = SrcLeaderboardModel.model_validate(leaderboard_data)

    game_info = Games.objects.only(
        "id",
        "idefaulttime",
        "ipointsmax",
        "defaulttime",
        "pointsmax",
    ).get(id=src_lb.game)

    category_info = Categories.objects.only("id", "name").get(id=src_lb.category)

    level_info = None
    if src_lb.level:
        level_info = Levels.objects.only("id", "name").get(id=src_lb.level)

    if src_lb.level is None:
        max_points = game_info.pointsmax
        if game_info.defaulttime == "realtime_noloads":
            LRT_FIX = True
    else:
        max_points = game_info.ipointsmax
        if game_info.idefaulttime == "realtime_noloads":
            LRT_FIX = True

    base_context = RunSyncContext(
        game_id=game_info.id,
        category_id=category_info.id,
        category_name=category_info.name,
        category_type=category_info.type,
        level_id=src_lb.level,
        level_name=level_info.name if level_info else None,
        wr_time_secs=0.0,
        max_points=max_points,
        default_time_type=src_lb.timing,
        subcategory_name="",
        download_pfp=False,
        lrt_fix=LRT_FIX,
        players_data=src_lb.players.data if src_lb.players else [],
        runs_data=src_lb.runs[0],
    )

    for lb_run in src_lb.runs:
        run_context = base_context.model_copy(update={"runs_data": lb_run})

        sync_run.delay(run_context)  # type:ignore


@shared_task(pydantic=True)
def sync_run(
    context_data: RunSyncContext,
) -> None:
    player_ids: list[str] = []

    place = context_data.runs_data.place
    run_data = context_data.runs_data.run
    if run_data.players is not None:
        try:
            platform = Platforms.objects.only("id").get(id=run_data.system.platform)
        except Platforms.DoesNotExist:
            platform = None

        try:
            approver = Players.objects.only("id").get(id=run_data.status.examiner)
        except Players.DoesNotExist:
            approver = None

        run_rta, run_nl, run_igt = time_conversion(run_data.times)

        default = {
            "runtype": "main" if run_data.level is None else "il",
            "game_id": run_data.game,
            "category_id": run_data.category,
            "subcategory": "",
            "place": place,
            "url": run_data.weblink,
            "video": run_data.video_uri,
            "date": run_data.date,
            "v_date": run_data.status.verify_date,
            "time": run_rta,
            "time_secs": run_data.times.realtime_t,
            "timenl": run_nl,
            "timenl_secs": run_data.times.realtime_noloads_t,
            "timeigt": run_igt,
            "timeigt_secs": run_data.times.ingame_t,
            "platform_id": platform,
            "emulated": run_data.system.emulated,
            "vid_status": run_data.status.status,
            "approver": approver,
            "description": run_data.comment,
        }

        if context_data.lrt_fix:
            default: dict = lrt_fix(default)

        base_wr_query = Runs.objects.filter(
            game=context_data.game_id,
            subcategory=context_data.subcategory_name,
            obsolete=False,
            place=1,
        )
        if context_data.category_type == "per-game":
            wr_pull = base_wr_query.filter(runtype="main").first()
        else:
            wr_pull = base_wr_query.filter(runtype="il").first()

        if place > 0:
            if place == 1:
                points = context_data.max_points
            else:
                wr_times = RunSyncTimesContext.model_validate(
                    wr_pull if wr_pull else run_data
                )

                if context_data.default_time_type == "realtime":
                    wr = (
                        wr_times.timeigt_secs
                        if wr_times.time_secs == 0
                        else wr_times.time_secs
                    )
                elif context_data.default_time_type == "realtime_noloads":
                    wr = wr_times.timenl_secs
                else:
                    wr = (
                        wr_times.time_secs
                        if wr_times.timeigt_secs == 0
                        else wr_times.timeigt_secs
                    )

                points = points_formula(
                    wr=wr,
                    run=run_data.times.primary_t,
                    max_points=context_data.max_points,
                )
        else:
            points = 0

        default["points"] = points

        for player_data in context_data.players_data:
            if player_data.id and player_data.rel == "user":
                player_ids.append(player_data.id)

        if run_data.level:
            default["level_id"] = run_data.level

        with transaction.atomic():
            run_obj, _ = Runs.objects.update_or_create(
                id=run_data.id,
                defaults=default,
            )

            RunPlayers.objects.filter(run=run_obj).delete()
            for order, player_id in enumerate(player_ids, start=1):
                RunPlayers.objects.create(
                    run=run_obj,
                    player_id=player_id,
                    order=order,
                )

        if len(run_data.values) > 0:
            for var_id, val_id in run_data.values.items():
                RunVariableValues.objects.update_or_create(
                    run=run_obj,
                    variable_id=var_id,
                    value_id=val_id,
                )

        if place >= 1:
            update_standings(
                is_wr=(place == 1),
                game_id=context_data.game_id,
                subcategory=context_data.subcategory_name,
                max_points=context_data.max_points,
                run_type=default["runtype"],
                default_time_type=context_data.default_time_type,
            )

        update_obsolete(
            game_id=context_data.game_id,
            subcategory=context_data.subcategory_name,
            players=run_data.players,
            run_type=default["runtype"],
            default_time_type=context_data.default_time_type,
        )

        for player in player_ids:
            sync_players(player)
