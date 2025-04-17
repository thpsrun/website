import re

from django import template
from django.db.models import Sum
from django.utils.timezone import now

from srl.models import Games, Players, Runs

register = template.Library()


@register.filter
def get_unique_game_names(main_runs):
    """Determines unique game names from an array."""
    game_names = set()
    unique_games = []

    for game in main_runs:
        if game.gameid not in game_names:
            game_names.add(game.gameid)
            unique_games.append(game)

    for game in unique_games:
        categories = []
        for run in main_runs:
            if run.gameid == game.gameid:
                categories.append(run.category)
        game.categories = categories

    return unique_games


@register.filter
def filter_game_name(game_runs, game_name):
    """Filters game names."""
    return [game for game in game_runs if Games.objects.get(id=game.game.id).name == game_name]


@register.filter
def custom_splitter(value):
    """Splits Django template variables."""
    match = re.search(r"[-(]", value)
    if not match:
        return [value.strip(), ""]

    index = match.start()
    symbol = value[index]

    first = value[:index].strip()
    second = value[index:].strip() if symbol == "(" else value[index + 1:].strip()

    return [first, second]


@register.filter
def trim(value):
    """Trims Django template variables."""
    return value.strip()


@register.filter
def get_rank(game_name, player_name):
    """Gets the current rank of a specific speedrun versus other runners."""
    players = Players.objects.only("id").all()
    leaderboard = []

    game_id  = Games.objects.get(name=game_name).id
    il_board = Runs.objects.only("id").filter(runtype="il", gameid=game_id).all()

    for player in players:
        il_points = (
            il_board.only("id", "points")
            .filter(playerid=player.id)
            .aggregate(total_points=Sum("points"))["total_points"] or 0
        )
        leaderboard.append({
            "player": player,
            "total_points": il_points
        })

    il_leaderboard = sorted(leaderboard, key=lambda x: x["total_points"], reverse=True)

    rank_start = 1
    for rank, item in enumerate(il_leaderboard, start=rank_start):
        item["rank"] = rank

    for entry in il_leaderboard:
        if entry["player"] == player_name:
            return entry


@register.filter
def time_since(value):
    """From value given, able to determine how long ago the instance has occurred."""
    if not value:
        return ""

    delta = now() - value

    days    = delta.days
    hours   = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if days and hours and minutes:
        return f"{days} days, {hours} hours and {minutes} minutes ago"
    elif days and hours:
        return f"{days} days and {hours} hours ago"
    elif days and minutes:
        return f"{days} days and {minutes} minutes ago"
    elif days:
        return f"{days} days ago"
    elif hours and minutes:
        return f"{hours} hours and {minutes} minutes ago"
    elif hours:
        return f"{hours} hours ago"
    elif minutes:
        return f"{minutes} minutes ago"
    else:
        return "Just now"
