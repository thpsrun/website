import os,environ

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