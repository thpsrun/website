from typing import Any, Optional

from django.core.paginator import Paginator
from django.db.models import Q, QuerySet, Sum
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import Players, Runs


def get_country_info(
    player: Players,
) -> tuple[Optional[str], Optional[str]]:
    """Returns the player's country ID and country name."""
    if player.countrycode:
        return player.countrycode.id, player.countrycode.name

    return None, None


def get_main_points(
    player: Players,
    runs_list: QuerySet["Runs"],
) -> int | None:
    """Returns the combined points of a player for full-game speedruns."""
    runs = runs_list.only(
        "id",
        "subcategory",
        "points",
    ).filter(Q(player_id=player) | Q(player2_id=player))

    # If a runner has been in multiple co-op speedruns, they *could* be player1 for one run
    # and player2 for the other; this makes it so only the run with the most points is counted.
    if runs.filter(subcategory__contains="Co-Op").exists():
        exclude = (
            runs.filter(subcategory__contains="Co-Op")
            .order_by("-points")
            .values("id")[1:]
        )
        runs = runs.exclude(id__in=exclude)

    runs = runs.only("points")
    return runs.aggregate(total_points=Sum("points"))["total_points"] or 0


def get_il_points(
    player: Players,
    runs_list: QuerySet["Runs"],
) -> int | None:
    """Returns the combined points of a player for individual level speedruns."""
    il_runs = runs_list.only("points").filter(player_id=player)

    return il_runs.aggregate(total_points=Sum("points"))["total_points"] or 0


def leaderboard_entry(
    player: Players,
    points: int,
    game: str = None,
) -> dict[dict, str]:
    """Returns contextual information about a runner in a simplified format."""
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
    players_all: list,
    runs_list: QuerySet["Runs"],
) -> list[dict[str, Any]]:
    """Returns a sorted leaderboard that is used to display ALL full-game speedrunners."""
    leaderboard = []

    for player in players_all:
        player_lookup = (
            Players.objects.select_related("countrycode").defer("awards").get(id=player)
        )
        points = get_main_points(player_lookup, runs_list)
        leaderboard.append(leaderboard_entry(player_lookup, points))

    return sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)


def profile_two(
    players_all: list,
    runs_list: QuerySet["Runs"],
) -> list[dict[str, Any]]:
    """Returns a sorted leaderboard that is used to display ALL individual level speedruns."""
    il_lb = []

    for player in players_all:
        player_lookup = (
            Players.objects.select_related("countrycode").defer("awards").get(id=player)
        )
        il_points = get_il_points(player_lookup, runs_list)
        if il_points > 0:
            il_lb.append(leaderboard_entry(player_lookup, il_points))

    return sorted(il_lb, key=lambda x: x["total_points"], reverse=True)


def profile_three(
    players_all: list,
    main_runs_all: QuerySet["Runs"],
    il_runs_all: QuerySet["Runs"],
) -> tuple[int, int]:
    """Returns a sorted leaderboard that combines both full-game and IL speedruns for players."""
    fg_lb = []
    il_lb = []

    for player in players_all:
        player_lookup = (
            Players.objects.select_related("countrycode").defer("awards").get(id=player)
        )
        main_points = get_main_points(player_lookup, main_runs_all)
        il_points = get_il_points(player_lookup, il_runs_all)

        if main_points > 0:
            fg_lb.append(leaderboard_entry(player_lookup, main_points))
        if il_points > 0:
            il_lb.append(leaderboard_entry(player_lookup, il_points))

    fg_lb = sorted(fg_lb, key=lambda x: x["total_points"], reverse=True)
    il_lb = sorted(il_lb, key=lambda x: x["total_points"], reverse=True)

    return fg_lb + il_lb, fg_lb, il_lb


def profile_four(
    players_all: list,
    runs_list: QuerySet["Runs"],
) -> tuple[list[dict[str, Any]], QuerySet[tuple[Any, Any]]]:
    """Returns a sorted leaderboard for all individual level speedruns and historical data."""
    il_lb = []

    for player in players_all:
        wr_count = runs_list.only("id").filter(player_id=player, place=1).count()
        if wr_count > 1:
            player_check = (
                Players.objects.select_related("countrycode")
                .defer("awards")
                .get(id=player)
            )
            countrycode, countryname = get_country_info(player_check)
            il_lb.append(
                {
                    "player": player_check.name,
                    "nickname": player_check.nickname,
                    "countrycode": countrycode,
                    "countryname": countryname,
                    "il_wrs": wr_count,
                }
            )

    il_wr_counts = sorted(
        il_lb,
        key=lambda x: x["il_wrs"],
        reverse=True,
    )

    il_runs_old = (
        runs_list.filter(points=100)
        .exclude(
            level_id="rdnoro6w"  # Excludes the Hippos Zoo goal cause everyone has WR
        )
        .order_by("date")
        .annotate(o_date=TruncDate("date"))
        .values_list("subcategory", "time", "o_date")
    )[:10]

    return il_wr_counts, il_runs_old


def overall_leaderboard(
    request: HttpRequest,
    players_all: list,
    main_runs_all: QuerySet["Runs"],
    il_runs_all: QuerySet["Runs"],
) -> HttpResponse:
    """Returns the "overall" leaderboard that combines all non-obsolete points for all players."""
    leaderboard = []

    for player in players_all:
        player_lookup = (
            Players.objects.select_related("countrycode").defer("awards").get(id=player)
        )
        main_points = get_main_points(player_lookup, main_runs_all)
        il_points = get_il_points(player_lookup, il_runs_all)
        total_points = main_points + il_points
        leaderboard.append(leaderboard_entry(player_lookup, total_points))

    leaderboard = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)
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

    players_all = list(
        all_runs.filter(player__isnull=False)
        .values_list("player__id", flat=True)
        .distinct()
    )

    if profile == 1:
        main_runs_all = all_runs.filter(runtype="main")

        return profile_one(
            players_all,
            main_runs_all,
        )
    elif profile == 2:
        il_runs_all = all_runs.filter(runtype="il")

        return profile_two(
            players_all,
            il_runs_all,
        )
    elif profile == 3:
        main_runs_all = all_runs.filter(runtype="main")
        il_runs_all = all_runs.filter(runtype="il")

        return profile_three(
            players_all,
            main_runs_all,
            il_runs_all,
        )
    elif profile == 4:
        il_runs_all = all_runs.filter(runtype="il")

        return profile_four(
            players_all,
            il_runs_all,
        )
    else:
        main_runs_all = all_runs.filter(runtype="main")
        il_runs_all = all_runs.filter(runtype="il")

        return overall_leaderboard(
            request,
            players_all,
            main_runs_all,
            il_runs_all,
        )
