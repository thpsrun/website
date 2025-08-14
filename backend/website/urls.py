import environ
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import HttpResponse, HttpResponseRedirect, redirect
from django.urls import include, path

env = environ.Env()
environ.Env.read_env()

admin.site.site_header = env("SITE_NAME")
admin.site.site_title = env("SITE_NAME")
admin.site.index_title = "Admin Panel"


def discord_redirect(
    request: HttpResponse,
) -> HttpResponseRedirect:
    """Return Discord when accessing `WEBSITE.com/discord`."""
    if env("DISCORD_URL"):
        return redirect(env("DISCORD_URL"))
    else:
        return redirect("/")


def twitch_redirect(
    request: HttpResponse,
) -> HttpResponseRedirect:
    """Return Twitch when accessing `WEBSITE.com/twitch`."""
    if env("TWITCH_URL"):
        return redirect(env("TWITCH_URL"))
    else:
        return redirect("/")


def twitter_redirect(
    request: HttpResponse,
) -> HttpResponseRedirect:
    """Return Twitter when accessing `WEBSITE.com/twitter`."""
    if env("TWITTER_URL"):
        return redirect(env("TWITTER_URL"))
    else:
        return redirect("/")


def youtube_redirect(
    request: HttpResponse,
) -> HttpResponseRedirect:
    """Return YouTube when accessing `WEBSITE.com/youtube`."""
    if env("YOUTUBE_URL"):
        return redirect(env("YOUTUBE_URL"))
    else:
        return redirect("/")


def bluesky_redirect(
    request: HttpResponse,
) -> HttpResponseRedirect:
    """Return Bluesky when accessing `WEBSITE.com/bluesky`."""
    if env("BLUESKY_URL"):
        return redirect(env("BLUESKY_URL"))
    else:
        return redirect("/")


def src_redirect(
    request: HttpResponse,
) -> HttpResponseRedirect:
    """Returns Speedrun.com when accessing `WEBSITE.com/src`."""
    return redirect(env("SRC_URL"))


urlpatterns = [
    path("illiad/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("", include("srl.urls")),
    path("docs/", include("guides.urls")),
    # REDIRECTS
    path("discord", discord_redirect, name="discord_redirect"),
    path("twitch", twitch_redirect, name="twitch_redirect"),
    path("twitter", twitter_redirect, name="twitter_redirect"),
    path("bluesky", bluesky_redirect, name="bluesky_redirect"),
    path("youtube", youtube_redirect, name="youtube_redirect"),
    path("src", src_redirect, name="src_redirect"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = urlpatterns + debug_toolbar_urls()

handler404 = "srl.static_views.page_not_found"
