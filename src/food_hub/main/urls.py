"""main app URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "",
        login_required(TemplateView.as_view(template_name="main/dashboard.html")),
        name="dashboard",
    ),
    path(
        "new_meal/",
        login_required(TemplateView.as_view(template_name="main/compose_meal.html")),
        name="create-meal",
    ),
]
