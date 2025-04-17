from django.urls import path

from .views import render_guides_list, render_markdown

urlpatterns = [
    path("<str:game>/", render_guides_list, name="render_doc"),
    path("<str:game>/<str:doc>", render_markdown, name="render_doc"),
]
