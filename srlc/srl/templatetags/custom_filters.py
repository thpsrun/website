from django import template
from django.db.models import Sum
from ..models import GameOverview,ILRuns,MainRuns,Players,CountryCodes

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
def get_category_name(categories, category_id):
    return categories.get(id=category_id).name

@register.filter
def filter_game_name(game_runs, game_name):
    return [game for game in game_runs if GameOverview.objects.get(id=game.game.id).name == game_name]

@register.filter
def get_game_boxart(games, game_id):
    game = games.get(id=game_id)
    return game.boxart

@register.filter
def is_il_cat(game_name):
    thps_games = ["Tony Hawk's Pro Skater", "Tony Hawk's Pro Skater 2", "Tony Hawk's Pro Skater 3", "Tony Hawk's Pro Skater 4", "Tony Hawk's Pro Skater 1+2"]
    return game_name in thps_games

@register.filter
def get_rank(game_name, player_name):
    players = Players.objects.all()
    leaderboard = []

    game_id  = GameOverview.objects.get(name=game_name).id
    il_board = ILRuns.objects.filter(gameid=game_id).all()

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
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_country(countrycode):
    country = CountryCodes.objects.filter(id=countrycode).values("name")[0]["name"]
    return country