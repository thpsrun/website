from django.urls import URLPattern, path

from api.api import ninja_api

urlpatterns: list[URLPattern] = [
    path("", ninja_api.urls),
]
