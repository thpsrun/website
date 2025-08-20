from django.urls import path, re_path

from api.standard import (
    Categories,
    Games,
    Levels,
    PlayerRecords,
    Players,
    Runs,
    Streams,
    Values,
    Variables,
)
from api.website import Web_Categories, Web_Leaderboard, Web_Main, Web_Levels

website_urlpatterns = [
    path("website/mainpage", Web_Main.API_Web_Main.as_view(), name="WebMainPage"),
    path(
        "website/categories/<str:id>",
        Web_Categories.API_Web_Categories.as_view(),
        name="WebCategories",
    ),
    path(
        "website/levels/<str:id>",
        Web_Levels.API_Web_Levels.as_view(),
        name="WebLevels",
    ),
    re_path(
        r"^website/leaderboard/(?P<gameid>[^/]+)/(?P<catid>[^/]+)(?:/(?P<subcats>.*))?$",
        Web_Leaderboard.API_Web_Leaderboard.as_view(),
        name="WebRuns",
    ),
]

standard_urlpatterns = [
    path("runs/<str:id>", Runs.API_Runs.as_view(), name="Runs"),
    path("players/<str:id>", Players.API_Players.as_view(), name="Players"),
    path(
        "players/<str:id>/pbs",
        PlayerRecords.API_PlayerRecords.as_view(),
        name="Player Records",
    ),
    path("games/<str:id>", Games.API_Games.as_view(), name="Games"),
    path("categories/<str:id>", Categories.API_Categories.as_view(), name="Categories"),
    path("variables/<str:id>", Variables.API_Variables.as_view(), name="Variables"),
    path("values/<str:id>", Values.API_Values.as_view(), name="Values"),
    path("levels/<str:id>", Levels.API_Levels.as_view(), name="Levels"),
    path("live", Streams.API_Streams.as_view(), name="Streams"),
]

urlpatterns = website_urlpatterns + standard_urlpatterns
