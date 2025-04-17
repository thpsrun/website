from django.urls import path

from .complex_views import (
    FG_Leaderboard,
    GameLeaderboard,
    IL_Leaderboard,
    ILGameLeaderboard,
    Leaderboard,
    MainPage,
    PlayerHistory,
    PlayerProfile,
    search_leaderboard,
)
from .static_views import FAQ, Changelog, PrivacyPolicy

urlpatterns = [
    path("", MainPage, name="Leaderboard"),
    path("privacy", PrivacyPolicy, name="PrivacyPolicy"),
    path("changelog", Changelog, name="Changelog"),
    path("faq", FAQ, name="FAQ"),
    path("overall", Leaderboard, name="Leaderboard"),
    # path("overall/<int:year>/", MonthlyLeaderboard, name="YearlyLeaderboard"),
    # path("overall/<int:year>/<int:month>", MonthlyLeaderboard, name="MonthlyLeaderboard"),
    path("fullgame", FG_Leaderboard, name="FullGameLeaderboard"),
    path("player/<str:name>", PlayerProfile, name="PlayerProfile"),
    path("player/<str:name>/history", PlayerHistory, name="PlayerHistory"),
    path("<str:slug>/", GameLeaderboard, name="CategorySelection"),
    path("<str:game_slug>/all", IL_Leaderboard, name="GameLeaderboard"),
    path("<str:slug>/ils", ILGameLeaderboard, name="CategorySelection"),
    path("lbs/search", search_leaderboard, name="search_leaderboard"),
]
