from django.urls import path
from .views import render_markdown

urlpatterns = [
    path("<str:game>/<str:doc>",render_markdown,name="render_doc"),
]