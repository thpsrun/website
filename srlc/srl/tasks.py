import os
import re
import time

import requests
from celery import shared_task
from django.db import transaction
from langcodes import standardize_tag

from .m_tasks import points_formula, src_api, time_conversion

# from .automations import *
from .models import (
    Categories,
    CountryCodes,
    Games,
    Levels,
    Platforms,
    Players,
    Runs,
    RunVariableValues,
    Variables,
    VariableValues,
)


@shared_task
def update_game(src_game):
    """Creates or updates a `Games` model object based on the `src_game` argument.

    Args:
        src_game (dict): Usually from Speedrun.com's API. This includes information about a specific
            game that will be imported in to the `Games` model.
    """
    src_game = src_api(f"https://speedrun.com/api/v1/games/{src_game}?embed=platforms")
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
                    "name"          : src_game["names"]["international"],
                    "slug"          : src_game["abbreviation"],
                    "release"       : src_game["release-date"],
                    "defaulttime"   : src_game["ruleset"]["default-time"],
                    "boxart"        : src_game["assets"]["cover-large"]["uri"],
                    "twitch"        : twitch_get,
                    "pointsmax"     : points_max,
                    "ipointsmax"    : ipoints_max,
                }
            )

            plat_names = [plat["id"] for plat in src_game["platforms"]["data"]]

            for plat in plat_names:
                game.platforms.add(plat)


@shared_task
def update_game_runs(game_id, reset):
    """Beginning of a function chain that updates (or resets) a specific game based upon its ID.

    Args:
        game_id (str): The game ID (presented through other functions) that will can
            (optionally) reset `Categories`, `Levels`, `Variables`, `VariableValues`,
            `RunVariableValues`, and `Runs`; get a lot of information from the Speedrun.com API;
            and is passed to other functions to update categories, levels, variables, and
            (ultimately) get all the runs.

        reset (int): Determines if all `Categories`, `Levels`, `Variables`, `VariableValues`,
            `RunVariableValues`, and `Runs` who matched the game_id arguemnt are reset.

    Calls:
        - `src_api`
        - `update_category`
        - `update_level`
        - `update_variable`
        - `update_category_runs`
    """
    if reset == 1:
        Categories.objects.filter(game=game_id).delete()
        Levels.objects.filter(game=game_id).delete()
        Variables.objects.filter(game=game_id).delete()
        VariableValues.objects.filter(var__game__id=game_id).delete()
        RunVariableValues.objects.filter(run__game__id=game_id).delete()
        Runs.objects.filter(game=game_id, obsolete=False).delete()

    game_check = src_api(
        f"https://speedrun.com/api/v1/games/"
        f"{game_id}?embed=platforms,levels,categories,variables"
    )

    if isinstance(game_check, dict):
        cat_check = game_check["categories"]["data"]
        for check in cat_check:
            update_category.delay(check, game_id)

        il_check = game_check["levels"]["data"]
        if len(il_check) > 0:
            for level in il_check:
                update_level.delay(level, game_id)

        var_check = game_check["variables"]["data"]
        if len(var_check) > 0:
            for variable in var_check:
                update_variable.delay(game_id, variable)

        for category in cat_check:
            update_category_runs.delay(game_id, category, il_check)


@shared_task
def update_category(category, game_id):
    """Creates or updates a `Categories` model object based on the `category` variable.

    Args:
        category (dict): Usually from Speedrun.com's API. Includes information about a specific
            category that will be imported into the `Categories` model.

        game_id (str): Used to call the specific `Games` object for the category.
    """
    with transaction.atomic():
        Categories.objects.update_or_create(
            id=category["id"],
            defaults={
                "name"  : category["name"],
                "game"  : Games.objects.only("id").get(id=game_id),
                "type"  : category["type"],
                "url"   : category["weblink"],
            }
        )


@shared_task
def update_platform(platform):
    """Creates or updates a `Platforms` model object based on the `platform` variable.

    Args:
        platform (dict): Usually from Speedrun.com's API. Includes information about a specific
            platform that will be imported into the `Platforms` model.
    """
    with transaction.atomic():
        Platforms.objects.update_or_create(
            id=platform["id"],
            defaults={
                "name" : platform["name"]
            }
        )


@shared_task
def update_level(level, game_id):
    """Creates or updates a `Levels` model object based on the `level` variable.

    Args:
        level (dict): Usually from Speedrun.com's API. Includes information about a specific level
            that will be imported into the `Levels` model.

        game_id (str): Used to call the specific `Games` object for the category.
    """
    with transaction.atomic():
        Levels.objects.update_or_create(
            id=level["id"],
            defaults={
                "name"  : level["name"],
                "game"  : Games.objects.only("id").get(id=game_id),
                "url"   : level["weblink"],
            }
        )


@shared_task
def update_variable(gameid, variable):
    """Creates or updates a `Variables` model object based on the `variable` variable.

    Args:
        gameid (str): Used to call the specific `Games` object for the category.
        variable (dict): Usually from Speedrun.com's API. Includes information about a specific
            variable that will be imported into the `Variables` model.

    Calls:
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
                "name"      : variable["name"],
                "game"      : Games.objects.only("id").get(id=gameid),
                "cat"       : cat_get,
                "all_cats"  : True if variable["category"] is None else False,
                "scope"     : variable["scope"]["type"],
            }
        )

    if variable["is-subcategory"]:
        for value in variable["values"]["values"]:
            update_variable_value.delay(variable, value)


@shared_task
def update_variable_value(variable, value):
    """Creates or updates a `VariableValues` model object based on the `value` variable.

    Args:
        variable (dict): Usually from Speedrun.com's API. Includes information about a specific
            variable.
        value (str): Used to specify the exact value ID of the value to link to `Variables`.
    """
    with transaction.atomic():
        VariableValues.objects.update_or_create(
            var=Variables.objects.get(id=variable["id"]),
            value=value,
            name=variable["values"]["values"][value]["label"],
        )


@shared_task
def update_category_runs(game_id, category, il_check):
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

    Calls:
        - `invoke_runs`
    """
    var_ids = Variables.objects.only("id").filter(cat=category["id"])
    global_cats = Variables.objects.only("id").filter(all_cats=True, game=game_id)

    global_fg_cats = (
        Variables.objects.only("id")
        .filter(all_cats=True, scope="full-game", game=game_id)
    )

    if category["type"] == "per-level":
        # THPS community does not have any sub-categories for levels (only 1 category).
        # This will need be updated later to make it more dynamic.
        per_level_check = Categories.objects.only("id").filter(game=game_id, type="per-level")

        for il in il_check:
            leaderboard = src_api(
                f"https://speedrun.com/api/v1/leaderboards/{game_id}"
                f"level/{il['id']}/{category['id']}?embed=players,game,category"
            )

            if len(per_level_check) > 1:
                var_name = il["name"] + " (" + category["name"] + ")"
                invoke_runs.delay(game_id, category, leaderboard, var_name)
            else:
                invoke_runs.delay(game_id, category, leaderboard, il["name"])
    elif len(global_fg_cats) > 1:
        # The uses cases for this code assumes you have, at max, 2 global subcategories.
        # Code would need be updated to correctly take advantage of more than 1.
        cat_list      = []
        var_name_list = []

        if len(global_fg_cats) == 2:
            global_cat_one = (
                VariableValues.objects.select_related("var")
                .only("name", "var", "value")
                .filter(var_id=global_fg_cats[0].id)
            )

            global_cat_two = (
                VariableValues.objects.select_related("var")
                .only("name", "var", "value")
                .filter(var_id=global_fg_cats[1].id)
            )

            for global_value_one in global_cat_one:
                var_name   = ""
                lb_string  = ""

                lb_string  = lb_string + f"var-{global_value_one.var.id}={global_value_one.value}&"
                var_name   = var_name + f"{global_value_one.name}, "

                for val in global_cat_two:
                    lb_string2  = lb_string + f"var-{val.var.id}={val.value}&"
                    var_name2   = var_name + f"{val.name}, "

                    cat_list.append(lb_string2.rstrip("&"))
                    var_name_list.append(category["name"] + " (" + var_name2.rstrip(", ") + ")")

        for index, lb_string in enumerate(cat_list):
            leaderboard = src_api(
                f"https://speedrun.com/api/v1/leaderboards/"
                f"{game_id}/category/{category['id']}?{lb_string}"
                f"&embed=players,game,category"
            )

            if leaderboard != 400:
                invoke_runs.delay(game_id, category, leaderboard, var_name_list[index])
    elif len(var_ids) == 1:
        var_value = (
            VariableValues.objects.select_related("var")
            .only("name", "var", "value")
            .filter(var=var_ids[0].id)
        )

        for var in var_value:
            lb_string     = f"var-{var.var.id}={var.value}"
            var_name      = f"{var.name}"
            cat_list      = []
            var_name_list = []
            lb_string2    = ""
            var_name2     = ""

            if len(global_cats) > 1:
                for global_cat in global_cats:
                    global_values = (
                        VariableValues.objects.select_related("var")
                        .only("name", "var", "value")
                        .filter(var=global_cat.id)
                    )

                    for global_value in global_values:
                        lb_string2 = f"var-{global_cat.id}={global_value.value}&"
                        var_name2  = f"{global_value.name}"

                        cat_list.append(lb_string2 + lb_string)
                        var_name_list.append(
                            category["name"] + " " + var_name
                            + "(" + var_name2 + ")"
                        )
            elif len(global_cats) == 1:
                global_values = (
                    VariableValues.objects.select_related("var")
                    .only("name", "var", "value")
                    .filter(var=global_cats[0].id)
                )

                for global_value in global_values:
                    lb_string2 = f"&var-{global_value.var.id}={global_value.value}"
                    var_name2  = f", {global_value.name}"

                    cat_list.append(lb_string + lb_string2)
                    var_name_list.append(
                        category["name"] + " ("
                        + var_name + var_name2 + ")"
                    )
            else:
                cat_list.append(lb_string)
                var_name_list.append(category["name"] + " (" + var_name + ")")

            for index, lb_string in enumerate(cat_list):
                leaderboard = src_api(
                    f"https://speedrun.com/api/v1/leaderboards/"
                    f"{game_id}/category/{category['id']}?{lb_string}"
                    f"&embed=players,game,category"
                )

                if leaderboard != 400:
                    invoke_runs.delay(game_id, category, leaderboard, var_name_list[index])

    elif len(var_ids) > 1:
        var_value_one = (
            VariableValues.objects.select_related("var")
            .only("name", "var", "value")
            .filter(var=var_ids[0].id)
        )

        var_value_two = (
            VariableValues.objects.select_related("var")
            .only("name", "var", "value")
            .filter(var=var_ids[1].id)
        )

        lb_string     = ""
        var_name      = ""
        cat_list      = []
        var_name_list = []
        lb_string2    = ""
        var_name2     = ""

        for variable in var_value_one:
            for var in var_value_two:
                lb_string  = f"var-{variable.var.id}={variable.value}&var-{var.var.id}={var.value}&"
                var_name   = f"{variable.name}, {var.name}, "

                if len(global_cats) > 1:
                    for global_cat in global_cats:
                        global_values = (
                            VariableValues.objects.only("name", "value")
                            .filter(var=global_cat.id)
                        )

                        for global_value in global_values:
                            lb_string2 = f"var-{global_cat.id}={global_value.value}&"
                            var_name2  = f"{global_value.name}"

                            cat_list.append(lb_string2 + lb_string)
                            var_name_list.append(
                                category["name"] + " "
                                + var_name + "(" + var_name2 + ")"
                            )
                elif len(global_cats) == 1:
                    global_values = (
                        VariableValues.objects.only("name", "value")
                        .filter(var=global_cats[0].id)
                    )

                    for global_value in global_values:
                        lb_string2 = f"&var-{global_value.var.id}={global_value.value}"
                        var_name2  = f", {global_value.name}"

                        cat_list.append(lb_string + lb_string2)
                        var_name_list.append(
                            category["name"] + " ("
                            + var_name + var_name2 + ")"
                        )
                else:
                    cat_list.append(lb_string.rstrip("&"))
                    var_name_list.append(
                        category["name"] + " ("
                        + var_name.rstrip(", ") + ")"
                    )

            for index, lb_string in enumerate(cat_list):
                leaderboard = src_api(
                    f"https://speedrun.com/api/v1/leaderboards/"
                    f"{game_id}/category/{category['id']}?{lb_string}"
                    f"&embed=players,game,category"
                )

                if leaderboard != 400:
                    invoke_runs.delay(game_id, category, leaderboard, var_name_list[index])
    elif category["type"] == "per-game" and len(var_ids) == 0:
        if len(global_cats) > 0:
            for global_cat in global_cats:
                cat_list        = []
                var_name_list   = []
                lb_string       = ""
                var_name        = ""

                global_values = (
                    VariableValues.objects.only("name", "value")
                    .filter(var=global_cat.id)
                )

                for global_value in global_values:
                    lb_string = f"var-{global_cat.id}={global_value.value}"
                    var_name  = f"{global_value.name}"

                    cat_list.append(lb_string)
                    var_name_list.append(category["name"] + " (" + var_name + ")")

                for index, lb_string in enumerate(cat_list):
                    leaderboard = src_api(
                        f"https://speedrun.com/api/v1/leaderboards/"
                        f"{game_id}/category/{category['id']}?{lb_string}"
                        f"&embed=players,game,category"
                    )

                    if leaderboard != 400:
                        invoke_runs.delay(game_id, category, leaderboard, var_name_list[index])
        else:
            leaderboard = src_api(
                f"https://speedrun.com/api/v1/leaderboards/{game_id}/category/"
                f"{category['id']}?embed=players,game,category"
            )

            if leaderboard != 400:
                invoke_runs.delay(game_id, category, leaderboard, category["name"])


@shared_task
def update_player(player, download_pfp=True):
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

    Calls:
        - `src_api`
    """
    player_data = src_api(f"https://speedrun.com/api/v1/users/{player}")

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

        location = player_data.get("location")
        country = location.get("country") if location is not None else None
        c_code = country.get("code") if country is not None else None

        cc = (
            standardize_tag(c_code.replace("/", "_"))
            if c_code is not None
            else None
        )

        if isinstance(cc, str) and cc.startswith("ca-"):
            cc = "ca"

        if cc is not None:
            cc_name = player_data.get("location").get("country").get("names").get("international")
            with transaction.atomic():
                CountryCodes.objects.update_or_create(
                    id=cc,
                    defaults={
                        "name" : cc_name
                    }
                )

        try:
            cc_get = CountryCodes.objects.only("id").get(id=cc)
        except CountryCodes.DoesNotExist:
            cc_get = None

        pronouns_get = player_data.get("pronouns")

        twitch_get = (
            player_data.get("twitch", {}).get("uri")
            if player_data.get("twitch") is not None else None
        )

        youtube_get = (
            player_data.get("youtube", {}).get("uri")
            if player_data.get("youtube") is not None else None
        )

        twitter_get = (
            player_data.get("twitter", {}).get("uri")
            if player_data.get("twitter") is not None else None
        )

        with transaction.atomic():
            Players.objects.update_or_create(
                id=player,
                defaults={
                    "name"          : player_data["names"]["international"],
                    "url"           : player_data["weblink"],
                    "countrycode"   : cc_get,
                    "pfp"           : file_path if download_pfp is True else None,
                    "pronouns"      : pronouns_get,
                    "twitch"        : twitch_get,
                    "youtube"       : youtube_get,
                    "twitter"       : twitter_get,
                }
            )


@shared_task
def invoke_runs(game_id, category, leaderboard, var_name=None):
    """Iterates through the `leaderboard` argument to process all runs within it to import.

    Processes the `leaderboard (dict)` argument to determine what the world record speedrun is,
    all of the subsequent speedruns, and places them into the `Runs` model.

    Args:
        game_id (str): Game ID that is used to lookup a variety of objects from various models.
        category (dict): Usually from Speedrun.com's API. Includes information about a specific
            category.
        leaderboard (dict): Includes all of the runs about a specific category and/or subcategory,
            to include the world record and subsequent speedruns.
        var_name (str): None is default. This is the full "name" for the category and/or subcategory
            combination. This will be deprecated in a future release.
    """
    if len(leaderboard["runs"]) > 0:
        wr_records = leaderboard["runs"][0]
        pb_records = leaderboard["runs"][1:]
        wr_players = wr_records["run"]["players"]
        game_get   = (
            Games.objects
            .only("id", "pointsmax", "ipointsmax", "defaulttime", "idefaulttime")
            .get(id=game_id)
        )

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
                    wr_video = videos.get("links", [])[0].get("uri")
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
                platform_get = (
                    Platforms.objects.only("id")
                    .get(id=wr_records["run"]["system"]["platform"])
                )
            except Platforms.DoesNotExist:
                platform_get = None

            try:
                approver_get = (
                    Players.objects.only("id")
                    .get(id=wr_records["run"]["status"]["examiner"])
                )
            except Players.DoesNotExist:
                approver_get = None

            wr_date = (
                wr_records["run"]["submitted"]
                if wr_records["run"]["submitted"]
                else wr_records["run"]["date"]
            )

            run_times   = wr_records["run"]["times"]

            c_rta, c_nl, c_igt = time_conversion(run_times)

            default = {
                "player"        : player_get,
                "game"          : game_get,
                "category"      : Categories.objects.only("id").get(id=category["id"]),
                "subcategory"   : var_name,
                "place"         : 1,
                "url"           : wr_records["run"]["weblink"],
                "video"         : wr_video,
                "date"          : wr_date,
                "v_date"        : wr_records["run"]["status"]["verify-date"],
                "time"          : c_rta,
                "time_secs"     : wr_records["run"]["times"]["realtime_t"],
                "timenl"        : c_nl,
                "timenl_secs"   : wr_records["run"]["times"]["realtime_noloads_t"],
                "timeigt"       : c_igt,
                "timeigt_secs"  : wr_records["run"]["times"]["ingame_t"],
                "points"        : wr_points,
                "platform"      : platform_get,
                "emulated"      : wr_records["run"]["system"]["emulated"],
                "obsolete"      : False,
                "vid_status"    : wr_records["run"]["status"]["status"],
                "approver"      : approver_get,
                "description"   : wr_records["run"]["comment"],
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
                default["level"] = Levels.objects.only("id").get(id=wr_records["run"]["level"])

                if game_get.idefaulttime == "realtime_noloads":
                    lrt_fix = True

            # LRT_TEMP_FIX
            # This is a temporary fix for an issue with the SRC API where runs that have LRT but
            # no RTA time will have the LRT set to RTA instead. Really dumb.
            if lrt_fix and default["time_secs"] > 0 and default["timenl_secs"] == 0:
                default["time"]         = "0"
                default["time_secs"]    = 0.0
                default["timenl"]       = c_nl
                default["timenl_secs"]  = wr_records["run"]["times"]["realtime_t"]

            with transaction.atomic():
                run_obj, _ = Runs.objects.update_or_create(
                    id=run_id,
                    defaults=default
                )

            # If the world record has specific variable:value pairs, this will get them and
            # place them into a special RunsVariableValues model that is linked back to the
            # record in question.
            if len(wr_records["run"]["values"]) > 0:
                for var_id, val_id in wr_records["run"]["values"].items():
                    variable = Variables.objects.get(id=var_id)
                    value = VariableValues.objects.get(value=val_id)

                    RunVariableValues.objects.update_or_create(
                        run=run_obj,
                        variable=variable,
                        value=value
                    )

        for pb in pb_records:
            if pb["place"] > 0:
                pb_players = pb["run"]["players"]

                if pb_players is not None:
                    for player in pb_players:
                        if player["rel"] != "guest":
                            invoke_players.delay(leaderboard["players"]["data"], player["id"])

                    run_id  = pb["run"]["id"]
                    player1 = pb_players[0].get("id")
                    player2 = (
                        pb_players[1]["id"]
                        if len(pb_players) > 1 and pb_players[1]["rel"] == "user"
                        else None
                    )

                    pb_secs = pb["run"]["times"]["primary_t"]
                    points  = points_formula(wr_secs, pb_secs, wr_points)

                    videos = pb.get("run").get("videos")
                    pb_video = (
                        videos["links"][0]["uri"]
                        if videos and videos.get("text") != "N/A"
                        else None
                    )

                    try:
                        player_get = Players.objects.only("id").get(id=player1)
                    except Players.DoesNotExist:
                        player_get = None

                    try:
                        platform_get = (
                            Platforms.objects.only("id")
                            .get(id=pb["run"]["system"]["platform"])
                        )
                    except Platforms.DoesNotExist:
                        platform_get = None

                    try:
                        approver_get = (
                            Players.objects.only("id")
                            .get(id=pb["run"]["status"]["examiner"])
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

                    default = {
                        "runtype"       : "main" if category["type"] == "per-game" else "il",
                        "player"        : player_get,
                        "game"          : game_get,
                        "category"      : Categories.objects.only("id").get(id=category["id"]),
                        "subcategory"   : var_name,
                        "place"         : pb["place"],
                        "url"           : pb["run"]["weblink"],
                        "video"         : pb_video,
                        "date"          : pb_date,
                        "v_date"        : pb["run"]["status"]["verify-date"],
                        "time"          : c_rta,
                        "time_secs"     : pb["run"]["times"]["realtime_t"],
                        "timenl"        : c_nl,
                        "timenl_secs"   : pb["run"]["times"]["realtime_noloads_t"],
                        "timeigt"       : c_igt,
                        "timeigt_secs"  : pb["run"]["times"]["ingame_t"],
                        "points"        : points,
                        "platform"      : platform_get,
                        "emulated"      : pb["run"]["system"]["emulated"],
                        "obsolete"      : False,
                        "vid_status"    : pb["run"]["status"]["status"],
                        "approver"      : approver_get,
                        "description"   : pb["run"]["comment"],
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
                        default["level"] = Levels.objects.only("id").get(id=pb["run"]["level"])

                        if game_get.idefaulttime == "realtime_noloads":
                            lrt_fix = True

                    # LRT_TEMP_FIX
                    # This is a temporary fix for an issue with the SRC API where runs that have LRT
                    # but no RTA time will have the LRT set to RTA instead. Really dumb.
                    if lrt_fix and default["time_secs"] > 0 and default["timenl_secs"] == 0:
                        default["time"]         = "0"
                        default["time_secs"]    = 0.0
                        default["timenl"]       = c_nl
                        default["timenl_secs"]  = pb["run"]["times"]["realtime_t"]

                    with transaction.atomic():
                        run_obj, _ = Runs.objects.update_or_create(
                            id=run_id,
                            defaults=default
                        )

                    # If the speedrun has specific variable:value pairs, this will get them and
                    # place them into a special RunsVariableValues model that is linked back to the
                    # run in question.
                    if len(pb["run"]["values"]) > 0:
                        for var_id, val_id in pb["run"]["values"].items():
                            variable = Variables.objects.get(id=var_id)
                            value = VariableValues.objects.get(value=val_id)

                            RunVariableValues.objects.update_or_create(
                                run=run_obj,
                                variable=variable,
                                value=value
                            )


@shared_task
def invoke_players(players_data, player=None):
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

            location = p_data.get("location")
            country = location.get("country") if location is not None else None
            c_code = country.get("code") if country is not None else None

            cc = (
                standardize_tag(c_code.replace("/", "_"))
                if c_code is not None
                else None
            )

            if isinstance(cc, str) and cc.startswith("ca-"):
                cc = "ca"

            if cc is not None:
                cc_name = p_data.get("location").get("country").get("names").get("international")

                with transaction.atomic():
                    CountryCodes.objects.update_or_create(
                        id=cc,
                        defaults={
                            "name" : cc_name,
                        }
                    )

            try:
                cc_get = CountryCodes.objects.only("id").get(id=cc)
            except CountryCodes.DoesNotExist:
                cc_get = None

            pronouns_get = p_data.get("pronouns")

            twitch_get = (
                p_data.get("twitch", {}).get("uri")
                if p_data.get("twitch") is not None else None
            )

            youtube_get = (
                p_data.get("youtube", {}).get("uri")
                if p_data.get("youtube") is not None else None
            )

            twitter_get = (
                p_data.get("twitter", {}).get("uri")
                if p_data.get("twitter") is not None else None
            )

            with transaction.atomic():
                Players.objects.update_or_create(
                    id=player,
                    defaults={
                        "name"        : p_data["names"]["international"],
                        "url"         : p_data["weblink"],
                        "countrycode" : cc_get,
                        "pfp"         : file_path,
                        "pronouns"    : pronouns_get,
                        "twitch"      : twitch_get,
                        "youtube"     : youtube_get,
                        "twitter"     : twitter_get,
                    }
                )


@shared_task
def import_obsolete(player, download_pfp=False):
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

    Calls:
        - `src_api`
        - `add_run`
    """
    from api.tasks import add_run

    run_data = src_api(f"https://speedrun.com/api/v1/runs?user={player}&max=200", True)

    if isinstance(run_data, dict) and run_data is not None:
        all_runs = run_data["data"]
        offset   = 0

        while run_data["pagination"]["max"] == run_data["pagination"]["size"]:
            offset += 200
            run_data = src_api(
                f"https://speedrun.com/api/v1/"
                f"runs?user={player}&max=200&offset={offset}?embed=players",
                True
            )

            all_runs.extend(run_data["data"])

        for run in all_runs:
            if run["status"]["status"] == "verified":
                if Games.objects.filter(id=run["game"]).exists():
                    if not Runs.objects.filter(id=run["id"]).exists():
                        if run["level"]:
                            lb_info = src_api(
                                f"https://speedrun.com/api/v1/leaderboards/"
                                f"{run['game']}/level/{run['level']}/{run['category']}"
                                f"?embed=game,category,level,players,variables"
                            )
                        elif len(run["values"]) > 0:
                            lb_variables = ""
                            for key, value in run["values"].items():
                                lb_variables += f"var-{key}={value}&"

                            lb_var = lb_variables.rstrip("&")

                            lb_info = src_api(
                                f"https://speedrun.com/api/v1/leaderboards/"
                                f"{run['game']}/category/{run['category']}?{lb_var}"
                                f"&embed=game,category,level,players,variables"
                            )
                        else:
                            lb_info = src_api(
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
                                points_reset, download_pfp
                            )
