from api.v1.routers.utils import game_categories_cache_key, game_levels_cache_key


def categories_adapter(
    request,
    game_id: str,
) -> str:
    return game_categories_cache_key(game_id)


def levels_adapter(
    request,
    level_id: str,
) -> str:
    return game_levels_cache_key(level_id)
