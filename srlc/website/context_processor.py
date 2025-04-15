import os

import environ

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
    base_docs_path = "/srlc/docs/"
    navbar_docs = []

    if not os.path.exists(base_docs_path):
        return {"navbar_docs": []}

    for game_dir in sorted(os.listdir(base_docs_path)):
        if ".github" not in game_dir:
            full_game_path = os.path.join(base_docs_path, game_dir)
            if os.path.isdir(full_game_path):
                pages = []
                for file in sorted(os.listdir(full_game_path)):
                    if file.endswith(".md"):
                        pages.append({
                            "title" : file.replace(".md","").replace("_", " ").title(),
                            "url"   : f"/docs/{game_dir}/{file}".replace(".md", "")
                        })
                
                if pages:
                    navbar_docs.append({
                        "game" : game_dir,
                        "pages": pages
                    })
    
    return {"navbar_docs": navbar_docs}