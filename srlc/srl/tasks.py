import os
import re
import time
from itertools import product

import requests
from celery import chain, shared_task
from django.db import transaction
from langcodes import standardize_tag

from .m_tasks import points_formula, src_api, time_conversion
from .models import (
    Categories,
    CountryCodes,
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


@shared_task
def update_game(
    src_game: dict[dict, dict],
) -> None:
    """Creates or updates a `Games` model object based on the `src_game` argument.

    Args:
        src_game (dict): Usually from Speedrun.com's API. This includes information about a specific
            game that will be imported in to the `Games` model.
    """
    src_game: dict[dict, str] = src_api(
        f"https://speedrun.com/api/v1/games/{src_game}?embed=platforms"
    )
    if isinstance(src_game, dict):
        twitch_get = (
            src_game.get("names").get("twitch")
            if src_game.get("names").get("twitch") is not None
            else None
        )

        points_max = (
            1000
            if "category extension" not in src_game["names"]["international"].lower()
            else 25
        )

        ipoints_max = (
            100
            if "category extension" not in src_game["names"]["international"].lower()
            else 25
        )

        with transaction.atomic():
            game, _ = Games.objects.update_or_create(
                id=src_game["id"],
                defaults={
                    "name": src_game["names"]["international"],
                    "slug": src_game["abbreviation"],
                    "release": src_game["release-date"],
                    "defaulttime": src_game["ruleset"]["default-time"],
                    "boxart": src_game["assets"]["cover-large"]["uri"],
                    "twitch": twitch_get,
                    "pointsmax": points_max,
                    "ipointsmax": ipoints_max,
                },
            )

            plat_names = [plat["id"] for plat in src_game["platforms"]["data"]]

            for plat in plat_names:
                game.platforms.add(plat)


@shared_task
def update_game_runs(
    game_id: str,
    reset: int,
) -> None:
    """Beginning of a function chain that updates (or resets) a specific game based upon its ID.

    Args:
        game_id (str): The game ID (presented through other functions) that will can
            (optionally) reset `Categories`, `Levels`, `Variables`, `VariableValues`,
            `RunVariableValues`, and `Runs`; get a lot of information from the Speedrun.com API;
            and is passed to other functions to update categories, levels, variables, and
            (ultimately) get all the runs.

        reset (int): Determines if all `Categories`, `Levels`, `Variables`, `VariableValues`,
            `RunVariableValues`, and `Runs` who matched the game_id arguemnt are reset.

    Called Functions:
        - `src_api`
        - `update_category`
        - `update_level`
        - `update_variable`
        - `update_category_runs`
        - `normalize_src`
    """
    from api.tasks import normalize_src  # Done to prevent issues with loops.

    # Within the Admin Panel, you will select "Reset Game Runs" if you want to reset all
    # non-obsolete runs. This essentially is a hard reset, and shouldn't be used often. When that
    # is selected, reset is set to 1, which deletes all related Categories, Levels, Variables,
    # VariableValues, RunVariableValues, and Runs.
    # However, if you choose "Update Game Runs" it will iterate through ALL runs within the game
    # (including obsolete) and update things accordingly.
    if reset == 1:
        RunVariableValues.objects.filter(run__game__id=game_id).delete()
        VariableValues.objects.filter(var__game__id=game_id).delete()
        Variables.objects.filter(game=game_id).delete()
        Categories.objects.filter(game=game_id).delete()
        Levels.objects.filter(game=game_id).delete()
        Runs.objects.filter(game=game_id, obsolete=False).delete()

        game_check: dict[dict, str] = src_api(
            f"https://speedrun.com/api/v1/games/"
            f"{game_id}?embed=platforms,levels,categories,variables"
        )

        if isinstance(game_check, dict):
            cat_check = game_check["categories"]["data"]
            for check in cat_check:
                chain(update_category.s(check, game_id))()

            il_check = game_check["levels"]["data"]
            if len(il_check) > 0:
                for level in il_check:
                    chain(update_level.s(level, game_id))()

            var_check = game_check["variables"]["data"]
            if len(var_check) > 0:
                for variable in var_check:
                    chain(update_variable.s(game_id, variable))()

            for category in cat_check:
                chain(update_category_runs.s(game_id, category, il_check))()
    else:
        all_runs = Runs.objects.only("id").filter(game=game_id)

        series_id = Series.objects.all().first().id
        series_info: dict[dict, str] = src_api(
            f"https://speedrun.com/api/v1/series/{series_id}/games?max=50"
        )
        series_list = []

        for game in series_info:
            series_list.append(game["id"])

        for run in all_runs:
            chain(normalize_src.s(run.id, series_list))()


@shared_task
def update_category(
    category: dict[dict, dict],
    game_id: str,
) -> None:
    """Creates or updates a `Categories` model object based on the `category` argument.

    Args:
        category (dict): Usually from Speedrun.com's API. Includes information about a specific
            category that will be imported into the `Categories` model.

        game_id (str): Used to call the specific `Games` object for the category.
    """
    with transaction.atomic():
        Categories.objects.update_or_create(
            id=category["id"],
            defaults={
                "name": category["name"],
                "game": Games.objects.only("id").get(id=game_id),
                "type": category["type"],
                "url": category["weblink"],
                "rules": category["rules"],
            },
        )


@shared_task
def update_platform(
    platform: dict[dict, dict],
) -> None:
    """Creates or updates a `Platforms` model object based on the `platform` argument.

    Args:
        platform (dict): Usually from Speedrun.com's API. Includes information about a specific
            platform that will be imported into the `Platforms` model.
    """
    with transaction.atomic():
        Platforms.objects.update_or_create(
            id=platform["id"], defaults={"name": platform["name"]}
        )


@shared_task
def update_level(
    level: dict[dict, dict],
    game_id: str,
) -> None:
    """Creates or updates a `Levels` model object based on the `level` argument.

    Args:
        level (dict): Usually from Speedrun.com's API. Includes information about a specific level
            that will be imported into the `Levels` model.

        game_id (str): Used to call the specific `Games` object for the category.
    """
    with transaction.atomic():
        Levels.objects.update_or_create(
            id=level["id"],
            defaults={
                "name": level["name"],
                "game": Games.objects.only("id").get(id=game_id),
                "url": level["weblink"],
                "rules": level["rules"],
            },
        )


@shared_task
def update_variable(
    gameid: str,
    variable: dict[dict, dict],
) -> None:
    """Creates or updates a `Variables` model object based on the `variable` argument.

    Args:
        gameid (str): Used to call the specific `Games` object for the category.
        variable (dict): Usually from Speedrun.com's API. Includes information about a specific
            variable that will be imported into the `Variables` model.

    Called Functions:
        - `update_variable_value`
    """
    cat_get = (
        None
        if variable["category"] is None
        else Categories.objects.only("id").get(id=variable["category"])
    )

    with transaction.atomic():
        Variables.objects.update_or_create(
            id=variable["id"],
            defaults={
                "name": variable["name"],
                "game": Games.objects.only("id").get(id=gameid),
                "cat": cat_get,
                "all_cats": True if variable["category"] is None else False,
                "scope": variable["scope"]["type"],
            },
        )

    if variable["is-subcategory"]:
        for value in variable["values"]["values"]:
            chain(update_variable_value.s(variable, value))()


@shared_task
def update_variable_value(
    variable: dict[dict, dict],
    value: str,
) -> None:
    """Creates or updates a `VariableValues` model object based on the `value` argument.

    Args:
        variable (dict): Usually from Speedrun.com's API. Includes information about a specific
            variable.
        value (str): Used to specify the exact value ID of the value to link to `Variables`.
    """
    with transaction.atomic():
        VariableValues.objects.update_or_create(
            value=value,
            defaults={
                "var": Variables.objects.get(id=variable["id"]),
                "name": variable["values"]["values"][value]["label"],
                "rules": variable["values"]["values"][value]["rules"],
            },
        )


@shared_task
def update_category_runs(
    game_id: str,
    category: dict[dict, dict],
    il_check: dict[dict, dict],
) -> None:
    """Iterates through all categories in the `category` argument to input into `Categories` model.

    Begins a function chain that will iterate through the `category` and its dictionary in order to
    find all possible category and sub-category variants within a specific game. Additionally, it
    will process the `subcategory` field that will eventually be imported into the `Runs` model, as
    well as setting up the variables necessary to access the category's specific leaderboard.

    Args:
        game_id (str): Game ID that is used to lookup `Variables` and `Categories`.
        category (dict): Usually from Speedrun.com's API. Includes information about a specific
            category to pass into `invoke_runs`.
        il_check (dict): When a category is set to `per-level`, `il_check` would be iterated
            through to pass into `invoke_runs`.

    Called Functions:
        - `src_api`
        - `invoke_runs`
    """

    def iterate_combinations(
        var_dict: dict,
    ) -> list:
        if not var_dict:
            return [[]]

        keys = list(var_dict.keys())
        values_lists = [var_dict[key] for key in keys]

        combinations = product(*values_lists)
        return [list(zip(keys, values)) for values in combinations]

    def get_variable_combinations(
        scope_types: dict[dict, str],
        variable_list: dict[dict, str],
    ) -> list:
        lb_list = {}

        for variable in variable_list:
            if not variable.get("is-subcategory"):
                continue

            if variable["scope"]["type"] not in scope_types:
                continue

            value_ids = list(variable["values"]["values"].keys())
            lb_list[variable["id"]] = value_ids

        return iterate_combinations(lb_list)

    def fetch_leaderboard(
        game_id: str,
        category_id: str,
        il_id: str = None,
        combo: str = None,
    ):
        base_url = "https://speedrun.com/api/v1/leaderboards/"
        if il_id:
            url = f"{base_url}{game_id}/level/{il_id}/{category_id}"
        else:
            url = f"{base_url}{game_id}/category/{category_id}"

        if combo:
            var_string = "&".join(f"var={var_id}-{val_id}" for var_id, val_id in combo)
            url += f"?{var_string}&embed=players,game,category"
        else:
            url += "?embed=players,game,category"

        return src_api(url)

    is_il = category["type"] == "per-level"
    scope_types = (
        {"global", "all-level", "single-level"} if is_il else {"global", "full-game"}
    )

    if is_il:
        for il in il_check:
            variable_list: dict[dict, str] = src_api(
                f"https://www.speedrun.com/api/v1/levels/{il['id']}/variables"
            )
            combo_list = get_variable_combinations(
                scope_types,
                variable_list,
            )

            if combo_list:
                for combo in combo_list:
                    leaderboard = fetch_leaderboard(
                        game_id,
                        category["id"],
                        il["id"],
                        combo,
                    )
                    chain(invoke_runs.s(game_id, category, leaderboard))()
            else:
                leaderboard = fetch_leaderboard(
                    game_id,
                    category["id"],
                    il["id"],
                )
                chain(
                    invoke_runs.s(
                        game_id,
                        category,
                        leaderboard,
                    )
                )()
    else:
        variable_list = src_api(
            f"https://www.speedrun.com/api/v1/categories/{category['id']}/variables"
        )
        combo_list = get_variable_combinations(
            scope_types,
            variable_list,
        )

        if combo_list:
            for combo in combo_list:
                leaderboard = fetch_leaderboard(
                    game_id,
                    category["id"],
                    combo,
                )
                chain(
                    invoke_runs.s(
                        game_id,
                        category,
                        leaderboard,
                    )
                )()
        else:
            leaderboard = fetch_leaderboard(game_id, category["id"])
            chain(
                invoke_runs.s(
                    game_id,
                    category,
                    leaderboard,
                )
            )()


@shared_task
def update_player(
    player: str,
    download_pfp: bool = True,
) -> None:
    """Processes a specific player into the Speedrun.com API to gather metdata.

    Gathers information about a specific player (based on the `player` varaible) and converts it
    into a format to either create or update a `Players` model object.

    *Note*:
    This is used from the admin panel to update a SPECIFIC player. `invoke_players` should be used
    if iterating an array.

    Args:
        player (str): The exact name or ID of a player to process into the Speedrun.com API.
        download_pfp (bool): True by default. When True, the profile picture of the player is
            downloaded and saved to local disk for caching.

    Called Functions:
        - `src_api`
    """
    player_data: dict[dict, str] = src_api(
        f"https://speedrun.com/api/v1/users/{player}"
    )

    if isinstance(player_data, dict) and player_data is not None:
        if player_data["assets"]["image"]["uri"] is not None and download_pfp:
            response = requests.get(player_data["assets"]["image"]["uri"])

            while response.status_code == 420 or response.status_code == 503:
                time.sleep(60)
                response = requests.get(player_data["assets"]["image"]["uri"])

            folder_path = "srl/static/pfp"
            os.makedirs(folder_path, exist_ok=True)

            file_name = f"{player}.jpg"
            file_path = os.path.join(folder_path, file_name)

            with open(file_path, "wb") as f:
                f.write(response.content)
        else:
            file_path = None

        location: dict = player_data.get("location")
        country: dict = location.get("country") if location is not None else None
        c_code: str = country.get("code") if country is not None else None

        cc = standardize_tag(c_code.replace("/", "_")) if c_code is not None else None

        if isinstance(cc, str) and cc.startswith("ca-"):
            cc = "ca"

        if cc is not None:
            cc_name = (
                player_data.get("location")
                .get("country")
                .get("names")
                .get("international")
            )
            with transaction.atomic():
                CountryCodes.objects.update_or_create(
                    id=cc,
                    defaults={"name": cc_name},
                )

        try:
            cc_get = CountryCodes.objects.only("id").get(id=cc)
        except CountryCodes.DoesNotExist:
            cc_get = None

        pronouns_get = player_data.get("pronouns")

        twitch_get = (
            player_data.get("twitch", {}).get("uri")
            if player_data.get("twitch") is not None
            else None
        )

        youtube_get = (
            player_data.get("youtube", {}).get("uri")
            if player_data.get("youtube") is not None
            else None
        )

        twitter_get = (
            player_data.get("twitter", {}).get("uri")
            if player_data.get("twitter") is not None
            else None
        )

        with transaction.atomic():
            Players.objects.update_or_create(
                id=player,
                defaults={
                    "name": player_data["names"]["international"],
                    "url": player_data["weblink"],
                    "countrycode": cc_get,
                    "pfp": file_path if download_pfp is True else None,
                    "pronouns": pronouns_get,
                    "twitch": twitch_get,
                    "youtube": youtube_get,
                    "twitter": twitter_get,
                },
            )
    else:
        raise AttributeError


@shared_task
def invoke_runs(
    game_id: str,
    category: dict,
    leaderboard: dict,
) -> None:
    """Iterates through the `leaderboard` argument to process all runs within it to import.

    Processes the `leaderboard (dict)` argument to determine what the world record speedrun is,
    all of the subsequent speedruns, and places them into the `Runs` model.

    Args:
        game_id (str): Game ID that is used to lookup a variety of objects from various models.
        category (dict): Usually from Speedrun.com's API. Includes information about a specific
            category.
        leaderboard (dict): Includes all of the runs about a specific category and/or subcategory,
            to include the world record and subsequent speedruns.

    Called Functions:
        - `invoke_players`
        - `points_formula`
        - `time_conversion`
    """

    def build_var_name(
        base_name: str,
        run_variables: dict[dict, str],
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

    if len(leaderboard["runs"]) > 0:
        wr_records = leaderboard["runs"][0]
        pb_records = leaderboard["runs"][1:]
        wr_players = wr_records["run"]["players"]
        game_get = Games.objects.only(
            "id", "pointsmax", "ipointsmax", "defaulttime", "idefaulttime"
        ).get(id=game_id)

        if "category extension" in wr_records["run"]["game"].lower():
            wr_points = game_get.pointsmax
            defaulttime = game_get.defaulttime
        elif wr_records["run"]["level"] is not None:
            wr_points = game_get.ipointsmax
            defaulttime = game_get.idefaulttime
        else:
            wr_points = game_get.pointsmax
            defaulttime = game_get.defaulttime

        if wr_players is not None:
            run_id = wr_records["run"]["id"]
            run_times = wr_records["run"]["times"]

            if defaulttime == "realtime":
                wr_secs = (
                    run_times["ingame_t"]
                    if run_times["realtime_t"] == 0
                    else run_times["realtime_t"]
                )
            elif defaulttime == "realtime_noloads":
                wr_secs = (
                    run_times["realtime_t"]
                    if run_times["realtime_noloads_t"] == 0
                    else run_times["realtime_noloads_t"]
                )
            else:
                wr_secs = (
                    run_times["realtime_t"]
                    if run_times["ingame_t"] == 0
                    else run_times["ingame_t"]
                )

            run = wr_records.get("run", {})
            videos = run.get("videos")

            try:
                if videos is not None and videos.get("text") != "N/A":
                    wr_video = videos.get("links", [])[-1].get("uri")
                else:
                    wr_video = None
            except Exception:
                wr_video = None

            player1 = wr_players[0].get("id")
            player2 = (
                wr_players[1]["id"]
                if len(wr_players) > 1 and wr_players[1]["rel"] == "user"
                else None
            )

            for player in wr_players:
                if player["rel"] != "guest":
                    invoke_players.delay(leaderboard["players"]["data"], player["id"])

            try:
                player_get = Players.objects.only("id").get(id=player1)
            except Players.DoesNotExist:
                player_get = None

            try:
                platform_get = Platforms.objects.only("id").get(
                    id=wr_records["run"]["system"]["platform"]
                )
            except Platforms.DoesNotExist:
                platform_get = None

            try:
                approver_get = Players.objects.only("id").get(
                    id=wr_records["run"]["status"]["examiner"]
                )
            except Players.DoesNotExist:
                approver_get = None

            wr_date = (
                wr_records["run"]["submitted"]
                if wr_records["run"]["submitted"]
                else wr_records["run"]["date"]
            )

            run_times = wr_records["run"]["times"]

            c_rta, c_nl, c_igt = time_conversion(run_times)

            if category["type"] == "per-level":
                level = Levels.objects.only("id", "name").get(
                    id=wr_records["run"]["level"]
                )
                if (
                    len(
                        Categories.objects.only("id").filter(
                            game=game_get.id, type="per-level"
                        )
                    )
                    > 1
                ):
                    var_level = f"{level.name} ({category["name"]})"
                else:
                    var_level = f"{level.name}"
                var_name = build_var_name(var_level, wr_records["run"]["values"])
            else:
                base_name = category["name"]
                var_name = build_var_name(base_name, wr_records["run"]["values"])

            default = {
                "runtype": "main" if category["type"] == "per-game" else "il",
                "player": player_get,
                "game": game_get,
                "category": Categories.objects.only("id").get(id=category["id"]),
                "subcategory": var_name,
                "place": 1,
                "url": wr_records["run"]["weblink"],
                "video": wr_video,
                "date": wr_date,
                "v_date": wr_records["run"]["status"]["verify-date"],
                "time": c_rta,
                "time_secs": wr_records["run"]["times"]["realtime_t"],
                "timenl": c_nl,
                "timenl_secs": wr_records["run"]["times"]["realtime_noloads_t"],
                "timeigt": c_igt,
                "timeigt_secs": wr_records["run"]["times"]["ingame_t"],
                "points": wr_points,
                "platform": platform_get,
                "emulated": wr_records["run"]["system"]["emulated"],
                "obsolete": False,
                "vid_status": wr_records["run"]["status"]["status"],
                "approver": approver_get,
                "description": wr_records["run"]["comment"],
            }

            lrt_fix = False
            if category["type"] == "per-game":
                if player2:
                    try:
                        player2_get = Players.objects.only("id").get(id=player2)
                    except Players.DoesNotExist:
                        player2_get = None

                    default["player2"] = player2_get

                if game_get.defaulttime == "realtime_noloads":
                    lrt_fix = True

            else:
                default["level"] = level

                if game_get.idefaulttime == "realtime_noloads":
                    lrt_fix = True

            # LRT_TEMP_FIX
            # This is a temporary fix for an issue with the SRC API where runs that have LRT but
            # no RTA time will have the LRT set to RTA instead. Really dumb.
            if lrt_fix and default["time_secs"] > 0 and default["timenl_secs"] == 0:
                default["time"] = "0"
                default["time_secs"] = 0.0
                default["timenl"] = c_nl
                default["timenl_secs"] = wr_records["run"]["times"]["realtime_t"]

            with transaction.atomic():
                run_obj, _ = Runs.objects.update_or_create(id=run_id, defaults=default)

            # If the world record has specific variable:value pairs, this will get them and
            # place them into a special RunsVariableValues model that is linked back to the
            # record in question.
            if len(wr_records["run"]["values"]) > 0:
                for var_id, val_id in wr_records["run"]["values"].items():
                    variable = Variables.objects.get(id=var_id)
                    value = VariableValues.objects.get(value=val_id)

                    RunVariableValues.objects.update_or_create(
                        run=run_obj, variable=variable, value=value
                    )

        for pb in pb_records:
            if pb["place"] > 0:
                pb_players = pb["run"]["players"]

                if pb_players is not None:
                    for player in pb_players:
                        if player["rel"] != "guest":
                            invoke_players.delay(
                                leaderboard["players"]["data"], player["id"]
                            )

                    run_id = pb["run"]["id"]
                    player1 = pb_players[0].get("id")
                    player2 = (
                        pb_players[1]["id"]
                        if len(pb_players) > 1 and pb_players[1]["rel"] == "user"
                        else None
                    )

                    pb_secs = pb["run"]["times"]["primary_t"]
                    points = points_formula(wr_secs, pb_secs, wr_points)

                    videos = pb.get("run").get("videos")
                    try:
                        if videos is not None and videos.get("text") != "N/A":
                            pb_video = videos.get("links", [])[-1].get("uri")
                        else:
                            pb_video = None
                    except Exception:
                        pb_video = None

                    try:
                        player_get = Players.objects.only("id").get(id=player1)
                    except Players.DoesNotExist:
                        player_get = None

                    try:
                        platform_get = Platforms.objects.only("id").get(
                            id=pb["run"]["system"]["platform"]
                        )
                    except Platforms.DoesNotExist:
                        platform_get = None

                    try:
                        approver_get = Players.objects.only("id").get(
                            id=pb["run"]["status"]["examiner"]
                        )
                    except Players.DoesNotExist:
                        approver_get = None

                    pb_date = (
                        pb["run"]["submitted"]
                        if pb["run"]["submitted"]
                        else pb["run"]["date"]
                    )

                    run_times = pb["run"]["times"]

                    c_rta, c_nl, c_igt = time_conversion(run_times)

                    if category["type"] == "per-level":
                        level = Levels.objects.only("id", "name").get(
                            id=pb["run"]["level"]
                        )

                        if (
                            len(
                                Categories.objects.only("id").filter(
                                    game=game_get.id, type="per-level"
                                )
                            )
                            > 1
                        ):
                            var_level = f"{level.name} ({category["name"]})"
                        else:
                            var_level = f"{level.name}"
                        var_name = build_var_name(var_level, pb["run"]["values"])
                    else:
                        base_name = category["name"]
                        var_name = build_var_name(base_name, pb["run"]["values"])

                    default = {
                        "runtype": "main" if category["type"] == "per-game" else "il",
                        "player": player_get,
                        "game": game_get,
                        "category": Categories.objects.only("id").get(
                            id=category["id"]
                        ),
                        "subcategory": var_name,
                        "place": pb["place"],
                        "url": pb["run"]["weblink"],
                        "video": pb_video,
                        "date": pb_date,
                        "v_date": pb["run"]["status"]["verify-date"],
                        "time": c_rta,
                        "time_secs": pb["run"]["times"]["realtime_t"],
                        "timenl": c_nl,
                        "timenl_secs": pb["run"]["times"]["realtime_noloads_t"],
                        "timeigt": c_igt,
                        "timeigt_secs": pb["run"]["times"]["ingame_t"],
                        "points": points,
                        "platform": platform_get,
                        "emulated": pb["run"]["system"]["emulated"],
                        "obsolete": False,
                        "vid_status": pb["run"]["status"]["status"],
                        "approver": approver_get,
                        "description": pb["run"]["comment"],
                    }

                    lrt_fix = False
                    if category["type"] == "per-game":
                        if player2:
                            try:
                                player2_get = Players.objects.only("id").get(id=player2)
                            except Players.DoesNotExist:
                                player2_get = None

                            default["player2"] = player2_get

                        if game_get.defaulttime == "realtime_noloads":
                            lrt_fix = True
                    else:
                        default["level"] = level

                        if game_get.idefaulttime == "realtime_noloads":
                            lrt_fix = True

                    # LRT_TEMP_FIX
                    # This is a temporary fix for an issue with the SRC API where runs that have LRT
                    # but no RTA time will have the LRT set to RTA instead. Really dumb.
                    if (
                        lrt_fix
                        and default["time_secs"] > 0
                        and default["timenl_secs"] == 0
                    ):
                        default["time"] = "0"
                        default["time_secs"] = 0.0
                        default["timenl"] = c_nl
                        default["timenl_secs"] = pb["run"]["times"]["realtime_t"]

                    with transaction.atomic():
                        run_obj, _ = Runs.objects.update_or_create(
                            id=run_id, defaults=default
                        )

                    # If the speedrun has specific variable:value pairs, this will get them and
                    # place them into a special RunsVariableValues model that is linked back to the
                    # run in question.
                    if len(pb["run"]["values"]) > 0:
                        for var_id, val_id in pb["run"]["values"].items():
                            variable = Variables.objects.get(id=var_id)
                            value = VariableValues.objects.get(value=val_id)

                            RunVariableValues.objects.update_or_create(
                                run=run_obj, variable=variable, value=value
                            )


@shared_task
def invoke_players(
    players_data: dict[dict, str],
    player: str = None,
) -> None:
    """Processes a specific player into the Speedrun.com API to gather metdata.

    Processes all of the metadata from a specific player, iterated through the `players_data`
    argument. This information is used to create or update a `Players` model object.

    Args:
        players_data (dict): The complete list of players usually imported from a Speedrun.com
            API "players" embed.
        player (str): None by default. This is the Speedrun.com ID of a specific player.
    """
    for p_data in players_data:
        player_id = p_data.get("id")
        if player_id == player:
            if p_data["assets"]["image"]["uri"] is not None:
                file_name = (
                    re.search(r"/user/([a-zA-Z0-9]+)", p_data["assets"]["image"]["uri"])
                ).group(1) + ".jpg"

                if not os.path.exists("srl/static/pfp/" + file_name):
                    response = requests.get(p_data["assets"]["image"]["uri"])

                    while response.status_code == 420 or response.status_code == 503:
                        time.sleep(60)
                        response = requests.get(p_data["assets"]["image"]["uri"])

                    folder_path = "srl/static/pfp"
                    os.makedirs(folder_path, exist_ok=True)

                    file_path = os.path.join(folder_path, file_name)

                    with open(file_path, "wb") as f:
                        f.write(response.content)
                else:
                    folder_path = "srl/static/pfp"
                    file_path = os.path.join(folder_path, file_name)
            else:
                file_path = None

            location: dict = p_data.get("location")
            country: dict = location.get("country") if location is not None else None
            c_code: str = country.get("code") if country is not None else None

            cc = (
                standardize_tag(c_code.replace("/", "_"))
                if c_code is not None
                else None
            )

            if isinstance(cc, str) and cc.startswith("ca-"):
                cc = "ca"

            if cc is not None:
                cc_name = (
                    p_data.get("location")
                    .get("country")
                    .get("names")
                    .get("international")
                )

                with transaction.atomic():
                    CountryCodes.objects.update_or_create(
                        id=cc,
                        defaults={
                            "name": cc_name,
                        },
                    )

            try:
                cc_get = CountryCodes.objects.only("id").get(id=cc)
            except CountryCodes.DoesNotExist:
                cc_get = None

            pronouns_get = p_data.get("pronouns")

            twitch_get = (
                p_data.get("twitch", {}).get("uri")
                if p_data.get("twitch") is not None
                else None
            )

            youtube_get = (
                p_data.get("youtube", {}).get("uri")
                if p_data.get("youtube") is not None
                else None
            )

            twitter_get = (
                p_data.get("twitter", {}).get("uri")
                if p_data.get("twitter") is not None
                else None
            )

            with transaction.atomic():
                Players.objects.update_or_create(
                    id=player,
                    defaults={
                        "name": p_data["names"]["international"],
                        "url": p_data["weblink"],
                        "countrycode": cc_get,
                        "pfp": file_path,
                        "pronouns": pronouns_get,
                        "twitch": twitch_get,
                        "youtube": youtube_get,
                        "twitter": twitter_get,
                    },
                )


@shared_task
def import_obsolete(
    player: str,
    download_pfp: bool = False,
):
    """Iterates through a player's ENTIRE speedrun.com history to find runs related to the series.

    Once presented with a player name or ID, this will iterate through that player's ENTIRE
    Speedrun.com history to find runs that belong to each game in the `Games` model. This includes
    all obsolete speedruns (speedruns that have been defeated by the same player), but does not
    include orphans (speedruns that no longer belongs to a category and subcategory). Once this is
    determined, these are then processed through `add_run` to place it into the `Runs` model.

    Args:
        player (str): The Speedrun.com username or ID of the player who has their obsolete runs
            being imported.
        download_pfp (bool): False by default. When set to True, this value will eventually enable
            another function to download the profile picture of the player.

    Called Functions:
        - `src_api`
        - `add_run`
    """
    from api.tasks import add_run  # Makes sure we don't get loops.

    run_data: dict[dict, str] = src_api(
        f"https://speedrun.com/api/v1/runs?user={player}&max=200", True
    )

    if isinstance(run_data, dict) and run_data is not None:
        all_runs = run_data["data"]
        offset = 0

        while run_data["pagination"]["max"] == run_data["pagination"]["size"]:
            offset += 200
            run_data: dict[dict, str] = src_api(
                f"https://speedrun.com/api/v1/"
                f"runs?user={player}&max=200&offset={offset}?embed=players",
                True,
            )

            all_runs.extend(run_data["data"])

        for run in all_runs:
            if run["status"]["status"] == "verified":
                if Games.objects.filter(id=run["game"]).exists():
                    if not Runs.objects.filter(id=run["id"]).exists():
                        if run["level"]:
                            lb_info: dict[dict, str] = src_api(
                                f"https://speedrun.com/api/v1/leaderboards/"
                                f"{run['game']}/level/{run['level']}/{run['category']}"
                                f"?embed=game,category,level,players,variables"
                            )
                        elif len(run["values"]) > 0:
                            lb_variables = ""
                            for key, value in run["values"].items():
                                lb_variables += f"var-{key}={value}&"

                            lb_var = lb_variables.rstrip("&")

                            lb_info: dict[dict, str] = src_api(
                                f"https://speedrun.com/api/v1/leaderboards/"
                                f"{run['game']}/category/{run['category']}?{lb_var}"
                                f"&embed=game,category,level,players,variables"
                            )
                        else:
                            lb_info: dict[dict, str] = src_api(
                                f"https://speedrun.com/api/v1/leaderboards/"
                                f"{run['game']}/category/{run['category']}"
                                f"?embed=game,category,level,players,variables"
                            )

                        if isinstance(lb_info, dict):
                            obsolete = True
                            points_reset = False
                            add_run.delay(
                                lb_info["game"]["data"],
                                run,
                                lb_info["category"]["data"],
                                lb_info["level"]["data"],
                                run["values"],
                                obsolete,
                                points_reset,
                                download_pfp,
                            )
