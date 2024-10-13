import os,environ
from django.contrib import admin
from django.shortcuts import render,redirect
from django.urls import path, include

env = environ.Env()
environ.Env.read_env()

admin.site.site_header = "thps.run"
admin.site.site_title  = "thps.run"
admin.site.index_title = "Admin Panel"

def discord_redirect(request):
    return redirect(env("DISCORD_URL"))

def twitch_redirect(request):
    return redirect(env("TWITCH_URL"))

def twitter_redirect(request):
    return redirect(env("TWITTER_URL"))
  
def youtube_redirect(request):
    return redirect(env("YOUTUBE_URL"))

def src_redirect(request):
    return redirect(env("SRC_URL"))

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", include("srl.urls")),
    #Redirects#
    path("discord",discord_redirect,name="discord_redirect"),
    path("twitch",twitch_redirect,name="twitch_redirect"),
    path("twitter",twitter_redirect,name="twitter_redirect"),
    path("youtube",youtube_redirect,name="youtube_redirect"),
    path("src",src_redirect,name="src_redirect"),
    path('debug', trigger_error),
]

handler404 = "srl.static_views.page_not_found"