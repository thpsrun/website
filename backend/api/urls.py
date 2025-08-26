from __future__ import annotations

from typing import List

from django.urls import URLPattern, path

from .api import ninja_api

urlpatterns: List[URLPattern] = [
    path("", ninja_api.urls),
]
