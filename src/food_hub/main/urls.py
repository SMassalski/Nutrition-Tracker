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
    path("meal/", login_required(views.MealView.as_view()), name="meal"),
    path(
        "recipes/",
        login_required(TemplateView.as_view(template_name="main/select_recipe.html")),
        name="recipe",
    ),
    path(
        "recipes/<slug:slug>",
        login_required(views.RecipeEditView.as_view()),
        name="recipe-edit",
    ),
    path(
        "settings/",
        TemplateView.as_view(template_name="main/settings.html"),
        name="settings",
    ),
    path("profile/", views.profile_view, name="profile"),
    path(
        "profile/done",
        login_required(TemplateView.as_view(template_name="main/profile_done.html")),
        name="profile-done",
    ),
    path(
        "settings/profile/",
        login_required(
            TemplateView.as_view(template_name="main/profile_settings.html")
        ),
        name="profile-settings",
    ),
    path(
        "settings/profile/weight_measurements",
        login_required(
            TemplateView.as_view(template_name="main/weight_measurements.html")
        ),
        name="profile-weight-measurements",
    ),
    path(
        "settings/account",
        login_required(
            TemplateView.as_view(template_name="main/account_settings.html")
        ),
        name="account-settings",
    ),
]
