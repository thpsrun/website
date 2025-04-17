import os

import environ
from srl.models import Games

env = environ.Env()
environ.Env.read_env()


def global_name(request):
    return {
        "ENV_WEBSITE_NAME"        : env("SITE_NAME"),
        "ENV_WEBSITE_AUTHOR"      : env("SITE_AUTHOR"),
        "ENV_WEBSITE_KEYWORDS"    : env("SITE_KEYWORDS"),
        "ENV_WEBSITE_DESCRIPTION" : env("SITE_DESCRIPTION"),
    }


def global_social_media(request):
    return {
        "ENV_DISCORD"   : env("DISCORD_URL"),
        "ENV_TWITCH"    : env("TWITCH_URL"),
        "ENV_YOUTUBE"   : env("YOUTUBE_URL"),
        "ENV_BLUESKY"   : env("BLUESKY_URL"),
        "ENV_TWITTER"   : env("TWITTER_URL"),
        "ENV_SRC"       : env("SRC_URL"),
    }


def navbar_docs(request):
    base_docs_path  = "/srlc/docs/"
    navbar_docs     = []
    game_list       = Games.objects.only("name", "slug", "release")\
                    .all().order_by("release")

    if not os.path.exists(base_docs_path):
        return {"navbar_docs": []}

    for game in game_list:
        if game.slug in (os.listdir(base_docs_path)):
            full_game_path = os.path.join(base_docs_path, game.slug)
            if os.path.isdir(full_game_path):
                navbar_docs.append({
                    "game" : game.slug,
                })

    return {"navbar_docs": navbar_docs}
