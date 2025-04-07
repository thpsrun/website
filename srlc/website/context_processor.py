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