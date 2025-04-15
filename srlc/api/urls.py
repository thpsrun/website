from django.urls import path

from .views import (
    API_Categories,
    API_Games,
    API_Levels,
    API_PlayerRecords,
    API_Players,
    API_Runs,
    API_Streams,
    API_Values,
    API_Variables,
)

urlpatterns = [
    path("runs/<str:id>/", API_Runs.as_view(), name="Runs"),
    path("players/<str:id>/", API_Players.as_view(), name="Players"),
    path("players/<str:id>/pbs", API_PlayerRecords.as_view(), name="Player Records"),
    path("games/<str:id>/", API_Games.as_view(), name="Games"),
    path("categories/<str:id>/", API_Categories.as_view(), name="Categories"),
    path("variables/<str:id>/", API_Variables.as_view(), name="Variables"),
    path("values/<str:id>/", API_Values.as_view(), name="Values"),
    path("levels/<str:id>/", API_Levels.as_view(), name="Levels"),
    path("live/", API_Streams.as_view(), name="Streams"),
]