"""main app URL Configuration"""
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "", TemplateView.as_view(template_name="main/dashboard.html"), name="dashboard"
    ),
    path(
        "new_meal/",
        TemplateView.as_view(template_name="main/compose_meal.html"),
        name="create-meal",
    ),
]
