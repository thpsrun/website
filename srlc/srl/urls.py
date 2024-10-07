from django.urls import path
from .complex_views import MainPage,PlayerProfile,Leaderboard,GameLeaderboard,IL_Leaderboard,FG_Leaderboard,RG_Leaderboard,search_leaderboard,ILGameLeaderboard,OL_Leaderboard,MonthlyLeaderboard
from .static_views import PrivacyPolicy,Changelog,FAQ,page_not_found

urlpatterns = [
    path("", MainPage, name="Leaderboard"),
    path("privacy", PrivacyPolicy, name="PrivacyPolicy"),
    path("changelog", Changelog ,name="Changelog"),
    path("faq", FAQ, name="FAQ"),
    path("overall", Leaderboard, name="Leaderboard"),
    path("overall/<int:year>/", MonthlyLeaderboard, name="YearlyLeaderboard"),
    path("overall/<int:year>/<int:month>", MonthlyLeaderboard, name="MonthlyLeaderboard"),
    path("regional", RG_Leaderboard, name="RegionalLeaderboard"),
    path("olympics", OL_Leaderboard, name="OlympicLeaderboard"),
    path("fullgame", FG_Leaderboard, name="FullGameLeaderboard"),
    path("player/<str:name>", PlayerProfile, name="PlayerProfile"),
    path("<str:abbr>/", GameLeaderboard, name="CategorySelection"),
    path("<str:game_abbr>/points", IL_Leaderboard, name="GameLeaderboard"),
    path("<str:abbr>/ils", ILGameLeaderboard, name="CategorySelection"),
    path("lbs/search", search_leaderboard, name="search_leaderboard"),
]