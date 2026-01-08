from api.routers.guides.guides import router as guides_router
from api.routers.guides.tags import router as tags_router

__all__ = [
    "guides_router",
    "tags_router",
]
