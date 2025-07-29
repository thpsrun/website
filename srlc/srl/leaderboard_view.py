from datetime import date
from typing import Any, Optional

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from srl.models import Players, Runs


def get_country_info(
    player: Players,
) -> tuple[Optional[str], Optional[str]]:
    if player.countrycode:
        return player.countrycode.id, player.countrycode.name

    return None, None


def get_main_points(
    player: Players,
    runs_list: list[Runs],
) -> int:
    runs = [
        run
        for run in runs_list
        if (run.player and run.player.id == player.id)
        or (run.player2 and run.player2.id == player.id)
    ]

    coop_runs = [run for run in runs if "Co-Op" in run.subcategory]
    if len(coop_runs) > 1:
        best_coop = sorted(coop_runs, key=lambda x: x.points, reverse=True)[:1]
        best_ids = {run.id for run in best_coop}
        runs = [
            run for run in runs if "Co-Op" not in run.subcategory or run.id in best_ids
        ]

    return sum(run.points for run in runs)


def get_il_points(
    player: Players,
    runs_list: list[Runs],
) -> int:
    il_runs = [run for run in runs_list if (run.player and run.player.id == player.id)]

    return sum(run.points for run in il_runs)


def leaderboard_entry(
    player: Players,
    points: int,
    game: str = None,
) -> dict[str, str | int | None]:
    countrycode, countryname = get_country_info(player)
    entry = {
        "player": player.name,
        "nickname": player.nickname,
        "countrycode": countrycode,
        "countryname": countryname,
        "total_points": points,
    }
    if game:
        entry["game"] = game

    return entry


def profile_one(
    players_all: list[Players],
    runs_list: list[Runs],
) -> list[dict[str, Any]]:
    leaderboard = []
    for player in players_all:
        points = get_main_points(player, runs_list)
        leaderboard.append(leaderboard_entry(player, points))

    return sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)


def profile_two(
    players_all: list[Players],
    runs_list: list[Runs],
) -> list[dict[str, Any]]:
    il_lb = []
    for player in players_all:
        il_points = get_il_points(player, runs_list)
        if il_points > 0:
            il_lb.append(leaderboard_entry(player, il_points))

    return sorted(il_lb, key=lambda x: x["total_points"], reverse=True)


def profile_three(
    players_all: list[Players],
    main_runs_all: list[Runs],
    il_runs_all: list[Runs],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    # fg_lb = []
    # il_lb = []
    all_lb = []
    for player in players_all:
        main_points = get_main_points(player, main_runs_all)
        il_points = get_il_points(player, il_runs_all)
        all_points = main_points + il_points

        """ if main_points > 0:
            fg_lb.append(leaderboard_entry(player, main_points))
        if il_points > 0:
            il_lb.append(leaderboard_entry(player, il_points)) """
        if all_points > 0:
            all_lb.append(leaderboard_entry(player, all_points))

    # fg_lb.sort(key=lambda x: x["total_points"], reverse=True)
    # il_lb.sort(key=lambda x: x["total_points"], reverse=True)
    all_lb.sort(key=lambda x: x["total_points"], reverse=True)

    return all_lb  # , fg_lb, il_lb


def profile_four(
    players_all: list[Players],
    runs_list: list[Runs],
) -> tuple[list[dict[str, Any]], list[tuple[str, float, date]]]:
    il_lb = []
    for player in players_all:
        wr_count = sum(
            1 for run in runs_list if run.player.id == player.id and run.place == 1
        )
        if wr_count > 1:
            countrycode, countryname = get_country_info(player)
            il_lb.append(
                {
                    "player": player.name,
                    "nickname": player.nickname,
                    "countrycode": countrycode,
                    "countryname": countryname,
                    "il_wrs": wr_count,
                }
            )
    il_wr_counts = sorted(il_lb, key=lambda x: x["il_wrs"], reverse=True)
    il_runs_old = [
        (run.subcategory, run.time, run.date.date())
        for run in runs_list
        if run.points == 100 and run.level.id != "rdnoro6w"
    ]
    il_runs_old.sort(key=lambda x: x[2])

    return il_wr_counts, il_runs_old[:10]


def overall_leaderboard(
    request: HttpRequest,
    players_all: list[Players],
    main_runs_all: list[Runs],
    il_runs_all: list[Runs],
) -> HttpResponse:
    leaderboard = []
    for player in players_all:
        main_points = get_main_points(player, main_runs_all)
        il_points = get_il_points(player, il_runs_all)
        total_points = main_points + il_points

        leaderboard.append(leaderboard_entry(player, total_points))

    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    paginator = Paginator(leaderboard, 50)
    page_number = request.GET.get("page")
    leaderboard_page = paginator.get_page(page_number)

    for i, item in enumerate(leaderboard_page, start=leaderboard_page.start_index()):
        item["rank"] = i

    return render(request, "srl/leaderboard.html", {"leaderboard": leaderboard_page})


def Leaderboard(
    request: HttpRequest,
    profile: int = None,
    game: str = None,
) -> HttpResponse:
    """Returns information depending upon the `profile` argument to be rendered dynamically.

    Simplified lookup function that takes into account different scenarios involving all `Players`
    and `Runs`.

    Args:
        profile (int): Used to determine which function should be utilized to return what data.
        game (str): None by default. This is the slug for a specific `Games` model object. This
            is usually used to filter out runs towards that specific game.

    Returns:
        profile: Sorted leaderboard (with additional contexts and information) is returned so it can
            be dynamically generated on the website.

    Called Functions:
        - `profile_one`
        - `profile_two`
        - `profile_three`
        - `profile_four`
        - `overall_leaderboard`
    """
    all_runs = (
        Runs.objects.exclude(
            vid_status__in=["new", "rejected"],
            place=0,
        )
        .select_related(
            "game",
            "category",
            "player",
            "player__countrycode",
            "player2",
            "player2__countrycode",
        )
        .defer(
            "variables",
            "platform",
            "description",
        )
        .filter(obsolete=False)
    )

    if game:
        all_runs = all_runs.filter(game__slug=game)

    players_all: list[Players] = (
        Players.objects.only(
            "id",
            "name",
            "countrycode",
            "nickname",
        )
        .select_related("countrycode")
        .all()
    )

    if profile == 1:
        main_runs_all: list[Runs] = list(all_runs.filter(runtype="main"))

        return profile_one(
            players_all,
            main_runs_all,
        )
    elif profile == 2:
        il_runs_all: list[Runs] = list(all_runs.filter(runtype="il"))

        return profile_two(
            players_all,
            il_runs_all,
        )
    elif profile == 3:
        main_runs_all: list[Runs] = list(all_runs.filter(runtype="main"))
        il_runs_all: list[Runs] = list(all_runs.filter(runtype="il"))

        return profile_three(
            players_all,
            main_runs_all,
            il_runs_all,
        )
    elif profile == 4:
        il_runs_all: list[Runs] = list(all_runs.filter(runtype="il"))

        return profile_four(
            players_all,
            il_runs_all,
        )
    else:
        main_runs_all: list[Runs] = list(all_runs.filter(runtype="main"))
        il_runs_all: list[Runs] = list(all_runs.filter(runtype="il"))

        return overall_leaderboard(
            request,
            players_all,
            main_runs_all,
            il_runs_all,
        )
