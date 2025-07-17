from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from srl.leaderboard_view import Leaderboard


def Tournament_LB(
    request: HttpRequest,
) -> HttpResponse:
    """View that displays a leaderboard the combined points for a runner for a specific IL game.

    This view gathers the combined point values of all runners across for a specific game's ILs
    and generates a dynamic webpage (to include searching).

    Args:
        slug (str): The slug (abbreviation) for a game from the `Games` model.

    Returns:
        render (request, template, context): Request is sent to a specific template, which includes
        the context needed to dynamically generate the webpage.
    """
    leaderboard = Leaderboard(request, 5, "thps34")

    paginator = Paginator(leaderboard, 50)
    page_number = request.GET.get("page")
    leaderboard_page = paginator.get_page(page_number)
    rank_start = leaderboard_page.start_index()

    for item in leaderboard_page:
        item["rank"] = rank_start
        rank_start += 1

    context = {
        "leaderboard": leaderboard_page,
        "game_name": "Tony Hawk's Pro Skater 3+4",
        "game_slug": "thps34",
    }

    return render(request, "srl/tourney_lb.html", context)
