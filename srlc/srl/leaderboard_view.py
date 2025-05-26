from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render

from .models import Games, Players, Runs


def get_country_info(player):
    """Returns the player's country ID and country name."""
    if player.countrycode:
        return player.countrycode.id, player.countrycode.name

    return None, None


def get_main_points(player, runs_list):
    """Returns the combined points of a player for full-game speedruns."""
    runs = runs_list.filter(Q(player_id=player.id) | Q(player2_id=player.id))

    # If a runner has been in multiple co-op speedruns, they *could* be player1 for one run
    # and player2 for the other; this makes it so only the run with the most points is counted.
    if runs.filter(subcategory__contains="Co-Op").exists():
        exclude = runs.filter(subcategory__contains="Co-Op").order_by("-points").values("id")[1:]
        runs = runs.exclude(id__in=exclude)

    return runs.aggregate(total_points=Sum("points"))["total_points"] or 0


def get_il_points(player, game_id, runs_list):
    """Returns the combined points of a player for individual level speedruns."""
    il_runs = runs_list.filter(player_id=player.id)

    if game_id:
        il_runs = il_runs.filter(game_id=game_id)

    return il_runs.aggregate(total_points=Sum("points"))["total_points"] or 0


def leaderboard_entry(player, points, game=None):
    """Returns contextual information about a runner in a simplified format."""
    countrycode, countryname = get_country_info(player)

    entry = {
        "player"        : player.name,
        "nickname"      : player.nickname,
        "countrycode"   : countrycode,
        "countryname"   : countryname,
        "total_points"  : points
    }

    if game:
        entry["game"] = game

    return entry


def profile_one(players_all, runs_list):
    """Returns a sorted leaderboard that is used to display ALL full-game speedrunners."""
    leaderboard = []

    for player in players_all:
        points = get_main_points(player, runs_list)
        leaderboard.append(leaderboard_entry(player, points))

    return sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)


def profile_two(players_all, games_all, runs_list, game):
    """Returns a sorted leaderboard that is used to display ALL individual level speedruns."""
    il_lb = []
    game_id = games_all.get(slug=game).id

    for player in players_all:
        il_points = get_il_points(player, game_id, runs_list)
        if il_points > 0:
            il_lb.append(leaderboard_entry(player, il_points))

    return sorted(il_lb, key=lambda x: x["total_points"], reverse=True)


def profile_three(players_all, main_runs_all, il_runs_all):
    """Returns a sorted leaderboard that combines both full-game and IL speedruns for players."""
    fg_lb = []
    il_lb = []

    for player in players_all:
        main_points = get_main_points(player, main_runs_all)
        il_points = get_il_points(player, None, il_runs_all)

        if main_points > 0:
            fg_lb.append(leaderboard_entry(player, main_points))
        if il_points > 0:
            il_lb.append(leaderboard_entry(player, il_points))

    fg_lb = sorted(fg_lb, key=lambda x: x["total_points"], reverse=True)
    il_lb = sorted(il_lb, key=lambda x: x["total_points"], reverse=True)

    return fg_lb + il_lb, fg_lb, il_lb


def profile_four(players_all, games_all, runs_list, game):
    """Returns a sorted leaderboard for all individual level speedruns and historical data."""
    il_lb = []
    game_id = games_all.get(slug=game).id
    il_runs = runs_list.filter(game_id=game_id)

    for player in players_all:
        wr_count = il_runs.filter(player_id=player.id, place=1).count()
        if wr_count > 1:
            countrycode, countryname = get_country_info(player)
            il_lb.append({
                "player"        : player.name,
                "nickname"      : player.nickname,
                "countrycode"   : countrycode,
                "countryname"   : countryname,
                "il_wrs"        : wr_count
            })

    il_wr_counts = sorted(il_lb, key=lambda x: x["il_wrs"], reverse=True)

    il_runs_old = (
        il_runs.filter(points=100)
        .exclude(level_id="rdnoro6w")
        .order_by("date")
        .annotate(o_date=TruncDate("date"))
        .values_list("subcategory", "time", "o_date")
    )[:10]

    return il_wr_counts, il_runs_old


def overall_leaderboard(request, players_all, main_runs_all, il_runs_all):
    """Returns the "overall" leaderboard that combines all non-obsolete points for all players."""
    leaderboard = []

    for player in players_all:
        main_points = get_main_points(player, main_runs_all)
        il_points = get_il_points(player, None, il_runs_all)
        total_points = main_points + il_points
        leaderboard.append(leaderboard_entry(player, total_points))

    leaderboard = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)
    paginator = Paginator(leaderboard, 50)
    page_number = request.GET.get("page")
    leaderboard_page = paginator.get_page(page_number)

    for i, item in enumerate(leaderboard_page, start=leaderboard_page.start_index()):
        item["rank"] = i

    return render(
        request, "srl/leaderboard.html", {"leaderboard": leaderboard_page}
    )


def Leaderboard(request, profile=None, game=None):
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
    players_all = Players.objects.only("id", "name", "nickname", "url", "countrycode").all()

    games_all = (
        Games.objects.only("id", "name", "slug", "release", "defaulttime", "idefaulttime").all()
    )

    main_runs_all = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"], place=0)
        .select_related(
            "game", "category", "player", "player_countrycode", "player2", "player2_countrycode"
        )
        .main()
        .filter(obsolete=False)
    )

    il_runs_all = (
        Runs.objects.exclude(vid_status__in=["new", "rejected"], place=0)
        .select_related(
            "game", "category", "player", "player_countrycode", "player2", "player2_countrycode"
        )
        .il()
        .filter(obsolete=False)
    )

    if profile == 1:
        return profile_one(players_all, main_runs_all)
    elif profile == 2:
        return profile_two(players_all, games_all, il_runs_all, game)
    elif profile == 3:
        return profile_three(players_all, main_runs_all, il_runs_all)
    elif profile == 4:
        return profile_four(players_all, games_all, il_runs_all, game)
    else:
        return overall_leaderboard(request, players_all, main_runs_all, il_runs_all)
