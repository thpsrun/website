import hashlib

from django.db.models import Max
from srl.models import Runs


def leaderboard_cache_key(
    game_id: str,
    category_id: str,
    subcategory: str,
    level_id: str | None = None,
) -> str:
    filters = {
        "game_id": game_id,
        "category_id": category_id,
    }

    if level_id is not None:
        filters["level_id"] = level_id

    latest_update = Runs.objects.filter(**filters).aggregate(
        latest=Max(
            "updated_at",
        )
    )["latest"]

    timestamp = latest_update.isoformat() if latest_update else "None"

    cache_key = [
        f"game:{game_id}",
        f"category:{category_id}",
        f"level:{level_id}" if level_id else "FG",
        f"subcategory:{subcategory}",
        f"timestamp:{timestamp}",
    ]

    cache_string = ":".join(cache_key)

    key = hashlib.md5(cache_string.encode()).hexdigest()

    return f"lb:{key}:{timestamp[:10]}"

def player_cache_key(
        
)