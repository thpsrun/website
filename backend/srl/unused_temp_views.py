from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from srl.leaderboard_view import Leaderboard

""" # Temporary for THPS3+4 Tournament used in leaderboard_view.py.
    elif profile == 5:
        level_ids = [
            "wj7z431w",  # Foundry
            "wp7x4e4w",  # Airport
            "wkk648xw",  # LA
            "920qe36d",  # College
            "9vm7njx9",  # San Francisco
            "w6qo5r6d",  # Shipyard
        ]

        end_time = datetime(
            2025, 7, 27, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("America/New_York")
        )

        il_runs_all: list[Runs] = list(
            Runs.objects.exclude(
                vid_status__in=["new", "rejected"],
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
            .filter(
                runtype="il",
                description__icontains="THPSTourney",
                level_id__in=level_ids,
                date__lt=end_time,
            )
        )

        best_runs: dict[tuple[int, int], Runs] = {}
        for run in il_runs_all:
            player_id = run.player.id
            level_id = run.level.id
            key = (player_id, level_id)

            if key not in best_runs or run.points > best_runs[key].points:
                best_runs[key] = run

        il_runs_formatted = list(best_runs.values())

        return profile_two(
            players_all,
            il_runs_formatted,
        ) """


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
