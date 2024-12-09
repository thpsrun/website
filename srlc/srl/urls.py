from django.urls import path
from .complex_views import MainPage,PlayerProfile,Leaderboard,GameLeaderboard,IL_Leaderboard,FG_Leaderboard,search_leaderboard,ILGameLeaderboard,MonthlyLeaderboard
from .static_views import PrivacyPolicy,Changelog,FAQ

urlpatterns = [
    path("", MainPage, name="Leaderboard"),
    path("privacy", PrivacyPolicy, name="PrivacyPolicy"),
    path("changelog", Changelog ,name="Changelog"),
    path("faq", FAQ, name="FAQ"),
    path("overall", Leaderboard, name="Leaderboard"),
    path("overall/<int:year>/", MonthlyLeaderboard, name="YearlyLeaderboard"),
    path("overall/<int:year>/<int:month>", MonthlyLeaderboard, name="MonthlyLeaderboard"),
    path("fullgame", FG_Leaderboard, name="FullGameLeaderboard"),
    path("player/<str:name>", PlayerProfile, name="PlayerProfile"),
    path("<str:abbr>/", GameLeaderboard, name="CategorySelection"),
    path("<str:game_abbr>/all", IL_Leaderboard, name="GameLeaderboard"),
    path("<str:abbr>/ils", ILGameLeaderboard, name="CategorySelection"),
    path("lbs/search", search_leaderboard, name="search_leaderboard"),
]