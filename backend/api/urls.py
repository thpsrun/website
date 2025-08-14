from django.urls import path

from backend.api.standard_views import (
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
    #  Website v1 endpoints
    path("v1/website/mainpage", name="Main_Page"),
    #  Standard v1 endpoints
    path("v1/runs/<str:id>", API_Runs.as_view(), name="Runs"),
    path("v1/players/<str:id>", API_Players.as_view(), name="Players"),
    path("v1/players/<str:id>/pbs", API_PlayerRecords.as_view(), name="Player Records"),
    path("v1/games/<str:id>", API_Games.as_view(), name="Games"),
    path("v1/categories/<str:id>", API_Categories.as_view(), name="Categories"),
    path("v1/variables/<str:id>", API_Variables.as_view(), name="Variables"),
    path("v1/values/<str:id>", API_Values.as_view(), name="Values"),
    path("v1/levels/<str:id>", API_Levels.as_view(), name="Levels"),
    path("v1/live", API_Streams.as_view(), name="Streams"),
]
