from types import SimpleNamespace
from typing import Any

from celery import chain, shared_task
from django.db import transaction
from django.db.models import Count
from srl.m_tasks import convert_time, points_formula, src_api, time_conversion
from srl.models import (
    Categories,
    Games,
    Levels,
    Platforms,
    Players,
    Runs,
    RunVariableValues,
    Series,
    Variables,
    VariableValues,
)
from srl.tasks import update_category, update_game, update_player, update_variable


@shared_task
def normalize_src(
    id,
    series_id_list=None,
) -> Any:
    """Normalizes information about a specific speedrun from the Speedrun.com API.

    Normalizes all information and metadata about a speedrun from the Speedrun.com API based on its
    ID. This also sets up a chain of functions to import this data into all related models within
    the database, including creating new objects as needed.

    Args:
        id (str): Unique Speedrun.com identifier for a specific speedrun. This ID is what you see
            at the end of a URL for a game (e.g. `12345678` at the end of
            `https://speedrun.com/game/run/<ID>`)

    Called Functions:
        - `update_game`
        - `update_player`
        - `update_level`
        - `update_variable`
        - `update_category`
        - `add_run`
    """

    if not series_id_list:
        series_id = Series.objects.all().first().id

        series_info = src_api(
            f"https://speedrun.com/api/v1/series/{series_id}/games?max=50"
        )
        series_id_list = []

        for game in series_info:
            series_id_list.append(game["id"])

    run_info = src_api(f"https://speedrun.com/api/v1/runs/{id}?embed=players")

    if run_info == 404:
        if Runs.objects.filter(id=id).exists():
            default = {"vid_status": "rejected"}
            with transaction.atomic():
                Runs.objects.update_or_create(id=id, defaults=default)
                return

    try:
        if run_info["game"] in series_id_list:
            if not Games.objects.only("id").filter(id=run_info["game"]).exists():
                chain(update_game.s(run_info["game"]))()

            for player in run_info["players"]["data"]:
                if player["rel"] != "guest":
                    if not Players.objects.only("id").filter(id=player["id"]).exists():
                        chain(update_player.s(player["id"]))()

            base_url = "https://speedrun.com/api/v1/leaderboards"

            if run_info["level"]:
                second_part = f"{run_info['game']}/level/{run_info['level']}"
            else:
                second_part = f"{run_info['game']}/category"

            params = []

            if run_info["values"]:
                params.extend(
                    [f"var-{key}={value}" for key, value in run_info["values"].items()]
                )

            params.append("embed=game,category,level,players,variables")
            query_string = "&".join(params)

            lb_info = src_api(
                f"{base_url}/{second_part}/{run_info['category']}?{query_string}"
            )

            for variable in lb_info["variables"]["data"]:
                chain(
                    update_variable.s(
                        run_info["game"],
                        variable,
                    )
                )()

            chain(
                update_category.s(lb_info["category"]["data"], run_info["game"]),
            )()

            finish = 0
            for run in lb_info["runs"]:
                if run["run"]["id"] == run_info["id"]:
                    chain(
                        add_run.s(
                            lb_info["game"]["data"],
                            run,
                            lb_info["category"]["data"],
                            lb_info["level"]["data"],
                            run_info["values"],
                            False,  # obsolete
                            True,  # point_reset
                            True,  # download_pfp
                        )
                    )()
                    finish = 1
                    continue

            # Games can have the option so that speedruns from other platforms or regions
            # do not offset and obsolete if they are slower. They are still in the SRC leaderboard
            # endpoint, but they are marked as a place of 0. This just helps set them up properly
            # to be imported and properly excluded later.
            if finish == 0:
                run_info["place"] = 0
                chain(
                    add_run.s(
                        lb_info["game"]["data"],
                        run_info,
                        lb_info["category"]["data"],
                        lb_info["level"]["data"],
                        run_info["values"],
                        True,  # obsolete
                        False,  # point_reset
                        True,  # download_pfp
                    )
                )()

            # Simple check to see if the run has information on individual levels. If not,
            # it returns False so the serializer better processes it.
            if run_info["level"]:
                return True
            else:
                return False
        else:
            return "invalid"
    except Exception:
        return "invalid"


@shared_task
def add_run(
    game,
    run,
    category,
    level,
    run_variables,
    obsolete=False,
    point_reset=True,
    download_pfp=True,
) -> None:
    """Retrieves and normalizes Speedrun.com API data before importing it into the database.

    Continues normalization of SRC API data from `normalize_src`, this is used to normalize the data
    for a single run before forwarding it to `invoke_single_run`.

    Args:
        game (dict): Speedrun.com information on a specific game.
        run (dict): Speedrun.com information on a specific run.
        category (dict): Speedrun.com information on a specific category.
        level (dict): Speedrun.com information on a specific level.
        run_variables (dict): Speedrun.com information on specific variables.
        obsolete (bool): Default is False. Determines if the runs should be marked as obsolete when
            they are imported into the database.
        point_reset (bool): Default is True. Determines if additonal functions should be ran to
            reset the point values of a specific subcategory.
        download_pfp (bool): Default is True. Determines if the profile pictures of the imported
            speedrun's player should also be downloaded locally.

    Called Functions:
        - `invoke_single_run`
    """

    def build_var_name(
        base_name,
        run_variables,
    ) -> str:
        if len(run_variables) > 0:
            var_name = base_name + " ("
            for key, value in run_variables.items():
                value_name = (
                    VariableValues.objects.only("name", "value").get(value=value).name
                )
                var_name += f"{value_name}, "

            return var_name.removesuffix(", ") + ")"
        else:
            return base_name

    if category["type"] == "per-level":
        if (
            len(Categories.objects.only("id").filter(game=game["id"], type="per-level"))
            > 1
        ):
            base_name = f"{level['name']} ({category["name"]})"
        else:
            base_name = f"{level['name']}"
            var_name = build_var_name(base_name, run_variables)
    else:
        base_name = category["name"]
        var_name = build_var_name(base_name, run_variables)

    chain(
        invoke_single_run.s(
            game["id"],
            category,
            run,
            var_name,
            obsolete,
            point_reset,
            download_pfp,
        )
    )()


@shared_task
def invoke_single_run(
    game_id,
    category,
    run,
    var_name=None,
    obsolete=False,
    point_reset=True,
    download_pfp=True,
) -> None:
    """Creates or updates a `Runs` object with Speedrun.com API information.

    Args:
        game (dict): Speedrun.com information on a specific game.
        run (dict): Speedrun.com information on a specific run.
        category (dict): Speedrun.com information on a specific category.
        var_name (str): Full subcategory name to be imported into the `subcategory` field.
        obsolete (bool): Default is False. Determines if the runs should be marked as obsolete when
            they are imported into the database.
        point_reset (bool): Default is True. Determines if additonal functions should be ran to
            reset the point values of a specific subcategory.
        download_pfp (bool): Default is True. Determines if the profile pictures of the imported
            speedrun's player should also be downloaded locally.

    Called Functions:
        - `convert_time`
        - `points_formula`
        - `remove_obsolete`
        - `update_points`
    """
    if not obsolete:
        players = run["run"]["players"]
        place = run["place"]
    else:
        run = {"run": run}
        if "data" in run.get("run", {}).get("players", {}):
            players = run["run"]["players"]["data"]
        else:
            players = run["run"]["players"]

        place = 0

    lrt_fix = False
    if run["run"]["level"] is not None:
        game_get = Games.objects.only("id", "idefaulttime", "ipointsmax").get(
            id=game_id
        )
        max_points = game_get.ipointsmax

        if game_get.idefaulttime == "realtime_noloads":
            lrt_fix = True
    else:
        game_get = Games.objects.only("id", "defaulttime", "pointsmax").get(id=game_id)
        max_points = game_get.pointsmax

        if game_get.defaulttime == "realtime_noloads":
            lrt_fix = True

    if players is not None:
        run_id = run["run"]["id"]
        secs = run["run"]["times"]["primary_t"]

        try:
            run_video = (
                run.get("run").get("videos").get("links")[-1].get("uri")
                if run.get("run").get("videos") is not None
                or run.get("run").get("videos").get("text") != "N/A"
                else None
            )
        except Exception:
            run_video = None

        try:
            platform_get = Platforms.objects.only("id").get(
                id=run["run"]["system"]["platform"]
            )
        except Platforms.DoesNotExist:
            platform_get = None

        try:
            approver_get = Players.objects.only("id").get(
                id=run["run"]["status"]["examiner"]
            )
        except Exception:
            approver_get = None

        run_date = (
            run["run"]["submitted"] if run["run"]["submitted"] else run["run"]["date"]
        )

        v_date = (
            run["run"]["status"].get("verify-date")
            if run["run"]["status"].get("verify-date") is not None
            else None
        )

        run_times = run["run"]["times"]

        c_rta, c_nl, c_igt = time_conversion(run_times)

        default = {
            "runtype": "main" if category["type"] == "per-game" else "il",
            "game": game_get,
            "category": Categories.objects.only("id").get(id=category["id"]),
            "subcategory": var_name,
            "place": place,
            "url": run["run"]["weblink"],
            "video": run_video,
            "date": run_date,
            "v_date": v_date,
            "time": c_rta,
            "time_secs": run["run"]["times"]["realtime_t"],
            "timenl": c_nl,
            "timenl_secs": run["run"]["times"]["realtime_noloads_t"],
            "timeigt": c_igt,
            "timeigt_secs": run["run"]["times"]["ingame_t"],
            "platform": platform_get,
            "emulated": run["run"]["system"]["emulated"],
            "obsolete": obsolete,
            "vid_status": run["run"]["status"]["status"],
            "approver": approver_get,
            "description": run["run"]["comment"],
        }

        # LRT_TEMP_FIX
        # This is a temporary fix for an issue with the SRC API where runs that have LRT but no RTA
        # time will have the LRT set to RTA instead. Really dumb.
        if lrt_fix and default["time_secs"] > 0 and default["timenl_secs"] == 0:
            default["time"] = "0"
            default["time_secs"] = 0.0
            default["timenl"] = convert_time(run["run"]["times"]["realtime_t"])
            default["timenl_secs"] = run["run"]["times"]["realtime_t"]

        if category["type"] == "per-game":
            reset_points = "Main"
            wr_pull = Runs.objects.filter(
                runtype="main",
                game=game_id,
                subcategory=var_name,
                obsolete=False,
                place=1,
            ).first()

            defaulttime = Games.objects.only("defaulttime").get(id=game_id).defaulttime
        else:
            reset_points = "IL"
            wr_pull = Runs.objects.filter(
                runtype="il",
                game=game_id,
                subcategory=var_name,
                obsolete=False,
                place=1,
            ).first()

            defaulttime = Games.objects.only("defaulttime").get(id=game_id).idefaulttime

        if not obsolete:
            if run["place"] == 1:
                points = max_points
            else:
                source = wr_pull if wr_pull else SimpleNamespace(**default)
                if defaulttime == "realtime":
                    wr_time = (
                        source.timeigt_secs
                        if source.time_secs == 0
                        else source.time_secs
                    )
                elif defaulttime == "realtime_noloads":
                    wr_time = source.timenl_secs
                else:
                    wr_time = (
                        source.time_secs
                        if source.timeigt_secs == 0
                        else source.timeigt_secs
                    )

                points = points_formula(wr_time, secs, max_points)
        else:
            points = 0

        player1 = players[0].get("id")
        player2 = (
            players[1].get("id")
            if len(players) > 1 and players[1]["rel"] == "user"
            else None
        )

        if player1:
            try:
                chain(update_player.s(player1, download_pfp)())

                player1 = Players.objects.only("id").get(id=player1)
            except Players.DoesNotExist:
                player1 = None

        default["player"] = player1

        if player2:
            try:
                chain(update_player.s(player2, download_pfp))()

                player2 = Players.objects.only("id").get(id=player2)
            except Players.DoesNotExist:
                player2 = None

            default["player2"] = player2

        if run.get("run").get("level"):
            default["level"] = Levels.objects.only("id").get(id=run["run"]["level"])

        if point_reset:
            default["points"] = points

        with transaction.atomic():
            run_obj, _ = Runs.objects.update_or_create(
                id=run_id,
                defaults=default,
            )

        if len(run["run"]["values"]) > 0:
            for var_id, val_id in run["run"]["values"].items():
                variable = Variables.objects.get(id=var_id)
                value = VariableValues.objects.get(value=val_id)

                RunVariableValues.objects.update_or_create(
                    run=run_obj, variable=variable, value=value
                )

        if point_reset:
            chain(update_points.s(game_id, var_name, max_points, reset_points))()

        if not obsolete:
            chain(remove_obsolete.s(game_id, var_name, players, reset_points))()


@shared_task
def update_points(
    game_id,
    subcategory,
    max_points,
    reset_points,
) -> None:
    """Retrieves all speedruns within a game and subcategory and resets placings and points.

    Retrieves all speedruns within a game's subcateogyr and resets the `place` field for that run,
    and updates their point totals whenever a new world record is achieved.

    Args:
        game_id (str): Speedrun.com ID for the game that `subcategory` belongs to.
        subcategory (str): Full category and subcategory name (e.g. `Any% (Beginner)` or `Any% No
            Warp Normal`).
        max_points (int): Maximum point total for a speedrun (usually 1000 for full-game and 100 for
            individual levels).
        reset_points (str): Can be `Main` or `IL`. This assists in determining type of query to be
            ran.
    """
    place = 1
    old_time = 0
    old_points = 0
    rank_count = 0

    # Dictionary to map default timing methods to the type of seconds used.
    time_columns = {
        "realtime": "time_secs",
        "realtime_noloads": "timenl_secs",
        "ingame": "timeigt_secs",
    }

    if reset_points == "Main":
        all_runs = Runs.objects.only(
            "place",
            "points",
            "time_secs",
            "timenl_secs",
            "timeigt_secs",
        ).filter(
            runtype="main",
            game=game_id,
            subcategory=subcategory,
            obsolete=False,
        )

        default_time = Games.objects.only("defaulttime").get(id=game_id).defaulttime
    else:
        all_runs = Runs.objects.only(
            "place",
            "points",
            "time_secs",
            "timenl_secs",
            "timeigt_secs",
        ).filter(
            runtype="il",
            game=game_id,
            subcategory=subcategory,
            obsolete=False,
        )

        default_time = Games.objects.only("idefaulttime").get(id=game_id).idefaulttime

    runs = all_runs.order_by(time_columns[default_time])
    wr_time = runs[0].__getattribute__(time_columns[default_time])

    # Logic here will iterate through the runs from the same subcategory that are not obsolete in
    # the same game. If it is WR, then it gets max_points; rank is incremented.
    # If it is not WR, then points are calculated based on the formula and the max_points of the
    # run. The place of the run would be place + rank_count; rank_count is reset to 1. Then saved.
    for run in runs:
        run_time = run.__getattribute__(time_columns[default_time])

        if run_time == 0:
            run_time = run.timeigt_secs

        if run_time == wr_time:
            run.place = place
            run.points = max_points

            old_points = max_points
            rank_count += 1
        elif run_time == old_time:
            run.place = place
            run.points = old_points

            rank_count += 1
        else:
            points = points_formula(wr_time, run_time, max_points)
            run.points = points

            if rank_count > 0:
                run.place = place + rank_count
                place += rank_count

                rank_count = 1
            else:
                place += 1
                run.place = place

            old_time = run_time
            old_points = points

        run.save(update_fields=["place", "points"])


@shared_task
def remove_obsolete(
    game_id,
    subcategory,
    players,
    run_type,
) -> None:
    """Updates speedrun entries that should be obsolete.

    Retrieves all current runs by the player (depending on `game_id`, `subcategory`, and `run_type`)
    and marks all slower runs as obsolete.

    Args:
        game_id (str): Speedrun.com ID for the game that `subcategory` belongs to.
        subcategory (str): Full category and subcategory name (e.g. `Any% (Beginner)` or `Any% No
            Warp Normal`).
        players (dict): Player(s) who are having their speedruns marked as obsolete.
        run_type (str): Can be `Main` or `IL`. This assists in determining type of query to be ran.
    """
    time_columns = {
        "realtime": "time_secs",
        "realtime_noloads": "timenl_secs",
        "ingame": "timeigt_secs",
    }

    for player in players:
        if player is not None and player["rel"] != "guest":
            # Checks the defaulttime from the Games model.
            # Once found, it will set the slowest_runs variable based on the game ID, whether it
            # is already obsolete, from the same player, in the same category.
            if run_type == "Main":
                default_time = (
                    Games.objects.only("defaulttime").get(id=game_id).defaulttime
                )
                all_runs = (
                    Runs.objects.prefetch_related("game", "player")
                    .only(
                        "id",
                        "game__id",
                        "player__id",
                        "subcategory",
                        "obsolete",
                        "time_secs",
                        "timenl_secs",
                        "timeigt_secs",
                    )
                    .filter(
                        runtype="main",
                        game=game_id,
                        player=player["id"],
                        subcategory=subcategory,
                        obsolete=False,
                    )
                )
            else:
                default_time = (
                    Games.objects.only("idefaulttime").get(id=game_id).idefaulttime
                )
                all_runs = (
                    Runs.objects.prefetch_related("game", "player")
                    .only(
                        "id",
                        "game__id",
                        "player__id",
                        "subcategory",
                        "obsolete",
                        "time_secs",
                        "timenl_secs",
                        "timeigt_secs",
                    )
                    .filter(
                        runtype="il",
                        game=game_id,
                        player=player["id"],
                        subcategory=subcategory,
                        obsolete=False,
                    )
                )

            duplicated_subcategories = (
                all_runs.values("subcategory")
                .annotate(count=Count("subcategory"))
                .filter(count__gt=1)
                .values("subcategory")
            )

            slowest_runs = all_runs.filter(
                subcategory__in=duplicated_subcategories
            ).order_by(f"-{time_columns[default_time]}")
            # Removes the newest time from the query,
            # then sets all other runs (should be one) to obsolete.
            if len(slowest_runs) > 0:
                last = slowest_runs.last()
                slowest_runs = slowest_runs.exclude(id=last)
                for new_obsolete in slowest_runs:
                    new_obsolete.obsolete = True
                    new_obsolete.save(force_update=True)
