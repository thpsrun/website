from django.urls import path
from .views import API_ProcessRuns,API_Runs,API_Players,API_Games,API_Categories,API_Variables,API_Values,API_Levels,API_NewRuns,API_NewWRs

urlpatterns = [
    path("import/<str:runid>/", API_ProcessRuns.as_view(), name="ProcessRuns"),
    path("runs/<str:runid>/", API_Runs.as_view(), name="Runs"),
    path("players/<str:player>/", API_Players.as_view(), name="Players"),
    path("games/<str:game>/", API_Games.as_view(), name="Games"),
    path("categories/<str:cat>/", API_Categories.as_view(), name="Categories"),
    path("variables/<str:variable>/", API_Variables.as_view(), name="Variables"),
    path("values/<str:value>/", API_Values.as_view(), name="Values"),
    path("levels/<str:level>/", API_Levels.as_view(), name="Levels"),
    path("newruns/<str:newruns>/", API_NewRuns.as_view(), name="NewRuns"),
    path("newwrs/<str:newwrs>/", API_NewWRs.as_view(), name="NewWRs"),
]