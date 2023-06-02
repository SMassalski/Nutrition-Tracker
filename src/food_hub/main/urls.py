"""main app URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView
from main.views import main as views

urlpatterns = [
    path(
        "",
        login_required(TemplateView.as_view(template_name="main/dashboard.html")),
        name="dashboard",
    ),
    path(
        "new_meal/",
        login_required(views.MealView.as_view()),
        name="create-meal",
    ),
    path(
        "settings/account",
        login_required(
            TemplateView.as_view(template_name="main/account_settings.html")
        ),
        name="account-settings",
    ),
    path("profile/", views.profile_view, name="profile"),
    path(
        "profile/done",
        login_required(TemplateView.as_view(template_name="main/profile_done.html")),
        name="profile-done",
    ),
]
