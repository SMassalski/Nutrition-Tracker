"""main app URL Configuration"""
from django.urls import path
from django.views.generic import TemplateView
from main.views.main import home

urlpatterns = [
    path("", home, name="dashboard"),
    path(
        "new_meal/",
        TemplateView.as_view(template_name="main/compose_meal.html"),
        name="create-meal",
    ),
]
