from srl.m_tasks import src_api


def init_series(
    series_id: str,
) -> None:
    src_games = src_api(f"https://speedrun.com/api/v1/series/{series_id}/games?max=50")
    if not isinstance(src_games, int):
        for game in src_games:
            print(game)
