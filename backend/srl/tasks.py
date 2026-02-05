import os
import time
from itertools import product

import requests
from celery import chain, shared_task
from django.core.management import call_command
from django.db import transaction
from langcodes import standardize_tag

from srl.models import (
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
from srl.utils import src_api


@shared_task
def update_game(
    src_game: str,
) -> None:
    """Creates or updates a `Games` model object based on the `src_game` argument.

    Arguments:
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

    Arguments:
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

    Arguments:
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

    Arguments:
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

    Arguments:
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

    Arguments:
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

    Arguments:
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

    Arguments:
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

    Arguments:
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
def build_streaks_task() -> None:
    """Daily task to check WR streak anniversaries and award bonus points."""
    call_command("build_streaks")
