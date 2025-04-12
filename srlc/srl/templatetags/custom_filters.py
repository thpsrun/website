from django import template
from django.db.models import Sum
from django.utils.timezone import now
from srl.models import GameOverview,Players,Runs

register = template.Library()

@register.filter
def get_unique_game_names(main_runs):
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
    return [game for game in game_runs if GameOverview.objects.get(id=game.game.id).name == game_name]

@register.filter
def get_rank(game_name, player_name):
    players = Players.objects.only("id").all()
    leaderboard = []

    game_id  = GameOverview.objects.get(name=game_name).id
    il_board = Runs.objects.only("id").filter(runtype="il",gameid=game_id).all()

    for player in players:
        il_points = il_board.filter(playerid=player.id).aggregate(total_points=Sum("points"))["total_points"] or 0
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
    if not value:
        return ""

    delta = now() - value

    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if delta.days > 0:
        hours += delta.days * 24

    if hours and minutes:
        return f"Started {hours} hours and {minutes} minutes ago"
    elif hours:
        return f"Started {hours} hours ago"
    elif minutes:
        return f"Started {minutes} minutes ago"
    else:
        return "Just now"