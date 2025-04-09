import environ
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static


env = environ.Env()
environ.Env.read_env()

admin.site.site_header = env("SITE_NAME")
admin.site.site_title  = env("SITE_NAME")
admin.site.index_title = "Admin Panel"

def discord_redirect(request):
    if (env("DISCORD_URL")):
        return redirect(env("DISCORD_URL"))
    else:
        return redirect("/")

def twitch_redirect(request):
    if (env("TWITCH_URL")):
        return redirect(env("TWITCH_URL"))
    else:
        return redirect("/")

def twitter_redirect(request):
    if (env("TWITTER_URL")):
        return redirect(env("TWITTER_URL"))
    else:
        return redirect("/")
  
def youtube_redirect(request):
    if (env("YOUTUBE_URL")):
        return redirect(env("YOUTUBE_URL"))
    else:
        return redirect("/")

def bluesky_redirect(request):
    if (env("BLUESKY_URL")):
        return redirect(env("BLUESKY_URL"))
    else:
        return redirect("/")

def src_redirect(request):
    return redirect(env("SRC_URL"))

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", include("srl.urls")),
    path("docs/", include("guides.urls")),
    # REDIRECTS
    path("discord",discord_redirect,name="discord_redirect"),
    path("twitch",twitch_redirect,name="twitch_redirect"),
    path("twitter",twitter_redirect,name="twitter_redirect"),
    path("bluesky",bluesky_redirect,name="bluesky_redirect"),
    path("youtube",youtube_redirect,name="youtube_redirect"),
    path("src",src_redirect,name="src_redirect"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "srl.static_views.page_not_found"