from .categories import categories_router
from .games import games_router
from .levels import levels_router
from .platforms import platforms_router
from .players import players_router
from .runs import runs_router
from .streams import streams_router
from .variables import variables_router

__all__ = [
    "categories_router",
    "games_router",
    "levels_router",
    "platforms_router",
    "players_router",
    "runs_router",
    "streams_router",
    "variables_router",
]
