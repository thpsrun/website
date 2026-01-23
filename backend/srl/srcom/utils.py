from typing import List

from celery import shared_task
from django.db.models import Count

from srl.m_tasks import convert_time, points_formula, src_api, time_conversion
from srl.models import Platforms, Players, Runs, VariableValues
from srl.srcom.schema.src import SrcRunsPlayers


def create_leaderboard_link(
    game_id: str,
    category_id: str,
    il_id: str | None,
    var_combo: str | None,
) -> dict:
    """Helper function that creates the SRC leaderboard link to be queried.

    Arguments:
        game_id (str): Unique SRC ID for a game.
        category_id (str): Unique SRC ID for a category.
        il_id (str | None): Unique SRC ID for a level.
        var_combo (str | None): Variable:value pair combination string to be queried.
    """
    base_url = "https://speedrun.com/api/v1/leaderboards/"
    if il_id:
        url: str = f"{base_url}{game_id}/level/{il_id}/{category_id}"
    else:
        url: str = f"{base_url}{game_id}/category/{category_id}"

    if var_combo:
        var_string: str = "&".join(
            f"var={var_id}-{val_id}" for var_id, val_id in var_combo
        )
        url += f"?{var_string}&embed=players,game,category"
    else:
        url += "?embed=players,game,category"

    return src_api(url)


def build_var_name(
    base_name: str,
    run_variables: dict,
) -> str:
    """Helper function that creates the subcategory name for a speedrun.

    Arguments:
        base_name (str): Usually the level or category name.
        run_variables (dict): Variable:value pairs within a run.
    """
    if len(run_variables) > 0:
        var_name = base_name + " ("
        for _, value in run_variables.items():
            value_name = (
                VariableValues.objects.only("name", "value").get(value=value).name
            )
            var_name += f"{value_name}, "

        return var_name.removesuffix(", ") + ")"
    else:
        return base_name


def lrt_fix(
    default: dict,
) -> dict:
    """Helper function that fixes an issue with the SRC API regarding LRT times set to RTA.

    This is a temporary function (hopefully) that fixes an SRC API issue where runs that have
    load-time removed (LRT) but no real-time (RTA), will have the LRT set to RTA instead.

    Arguments:
        default (dict): Dictionary information about a specific run.

    Returns:
        default (dict): Fixed dictionary information about a specific run.
    """
    if default["time_secs"] > 0 and default["timenl_secs"] == 0:
        default["timenl"] = convert_time(default["time_secs"])
        default["timenl_secs"] = default["time_secs"]
        default["time"] = "0"
        default["time_secs"] = 0.0

    return default


@shared_task(pydantic=True)
def update_standings(
    is_wr: bool,
    game_id: str,
    subcategory: str,
    max_points: int,
    run_type: str,
    default_time_type: str,
) -> None:
    """Helper function that handles updating a leaderboard's points and rankings upon a record.

    Whenever a new world record is achieved, that record would then become the top place (1). All
    subsequent runs would need to be re-ranked and their points be algorithmically fixed.

    Arguments:
        is_wr (bool): When `True`, it will re-evaluate all points within the category. If `False`,
            then the point re-evaluation is ignored.
        game_id (str): Unique SRC ID of the game.
        subcategory (str): Subcategory string (e.g. "Any% No Warp Normal").
        max_points (int): Maximum number of points within the speedrun.
        run_type (str): Type of run that needs to be queried (e.g. "main" or "il").
        default_time_type (str): Default time type of the record.
    """
    current_place = 1
    tied_placements = 0
    previous_time = None
    runs_list: list = []

    # Dictionary to map default timing methods to the type of seconds used.
    time_columns = {
        "realtime": "time_secs",
        "realtime_noloads": "timenl_secs",
        "ingame": "timeigt_secs",
    }

    base_category_runs = Runs.objects.only(
        "place",
        "points",
        "time_secs",
        "timenl_secs",
        "timeigt_secs",
    ).filter(
        game=game_id,
        subcategory=subcategory,
        obsolete=False,
    )

    all_category_runs = base_category_runs.filter(runtype=run_type)
    runs = all_category_runs.order_by(time_columns[default_time_type])
    wr_time = getattr(runs[0], (time_columns[default_time_type]))

    for run in runs:
        run_time = getattr(run, (time_columns[default_time_type]))

        if is_wr:
            if run_time == wr_time:
                points = max_points
            else:
                points = points_formula(
                    wr=wr_time,
                    run=run_time,
                    max_points=max_points,
                )
        else:
            points = run.points

        if previous_time is not None and run_time != previous_time:
            current_place += tied_placements
            tied_placements = 0

        run.place = current_place
        run.points = points
        runs_list.append(run)

        tied_placements += 1
        previous_time = run_time

    Runs.objects.bulk_update(runs_list, ["place", "points"])


@shared_task(pydantic=True)
def update_obsolete(
    game_id: str,
    subcategory: str,
    players: List[SrcRunsPlayers],
    run_type: str,
    default_time_type: str,
) -> None:
    """Helper function that, when a new run is submitted, will mark all older runs as obsolete.

    When a speedrun is added to the leaderboard, this function will find all of their old runs
    that have NOT been marked and perform logic to determine which is faster. The fastest time
    is removed, with all remaining runs (which should be one) to be markedas obsolete.

    Arguments:
        game_id (str): Unique SRC ID of the game.
        subcategory (str): Subcategory string (e.g. "Any% No Warp Normal").
        players (List[SrcRunsPlayers]): Pydantic list of players passed onto the function.
        run_type (str): Type of run that needs to be queried (e.g. "main" or "il").
        default_time_type (str): Default time type of the record.
    """
    obsolete_runs: list = []

    # Dictionary to map default timing methods to the type of seconds used.
    time_columns = {
        "realtime": "time_secs",
        "realtime_noloads": "timenl_secs",
        "ingame": "timeigt_secs",
    }

    base_runs_query = (
        Runs.objects.select_related("game")
        .prefetch_related("run_players__player")
        .only(
            "id",
            "game__id",
            "subcategory",
            "obsolete",
            "time_secs",
            "timenl_secs",
            "timeigt_secs",
        )
        .filter(
            run_type=run_type, game_id=game_id, subcategory=subcategory, obsolete=False
        )
    )

    for player in players:
        if player is not None and player.rel != "guest":
            player_runs = base_runs_query.filter(run_players__player__id=player.id)

            duplicate_subcats = (
                player_runs.values("subcategory")
                .annotate(count=Count("subcategory"))
                .filter(count__gt=1)
            )

            slowest_runs = player_runs.filter(
                subcategory__in=duplicate_subcats
            ).order_by(f"-{time_columns[default_time_type]}")

            if len(slowest_runs) > 0:
                best_time = slowest_runs.last()
                slowest_runs = slowest_runs.exclude(id=best_time)

                for new_obsolete in slowest_runs:
                    new_obsolete.obsolete = True
                    obsolete_runs.append(new_obsolete.id)

    if obsolete_runs:
        Runs.objects.filter(id__in=obsolete_runs).update(obsolete=True)


def create_run_default(
    run_data: dict,
    subcategory_name: str,
    place: int,
    lrtfix: bool,
) -> dict:
    try:
        platform = Platforms.objects.only("id").get(id=run_data["system"]["platform"])
    except Platforms.DoesNotExist:
        platform = None

    try:
        approver = Players.objects.only("id").get(id=run_data["status"]["examiner"])
    except Players.DoesNotExist:
        approver = None

    run_rta, run_nl, run_igt = time_conversion(run_data["times"])

    default = {
        "runtype": "main" if run_data["level"] is None else "il",
        "game_id": run_data["game"],
        "category_id": run_data["category"],
        "subcategory": subcategory_name,
        "place": place,
        "url": run_data["weblink"],
        "video": run_data["video_uri"],
        "date": run_data["date"],
        "v_date": run_data["status"]["verify_date"],
        "time": run_rta,
        "time_secs": run_data["times"]["realtime_t"],
        "timenl": run_nl,
        "timenl_secs": run_data["times"]["realtime_noloads_t"],
        "timeigt": run_igt,
        "timeigt_secs": run_data["times"]["ingame_t"],
        "platform_id": platform.id if platform else None,
        "emulated": run_data["system"]["emulated"],
        "vid_status": run_data["status"]["status"],
        "approver": approver,
        "description": run_data["comment"],
    }

    if lrtfix:
        default: dict = lrt_fix(default)

    return default
