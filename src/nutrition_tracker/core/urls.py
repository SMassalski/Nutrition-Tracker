"""core app URL Configuration"""
from core.decorators import profile_required
from core.views import main as views
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "",
        profile_required(TemplateView.as_view(template_name="core/dashboard.html")),
        name="dashboard",
    ),
    path("meal/", profile_required(views.MealView.as_view()), name="meal"),
    path(
        "recipes/",
        profile_required(TemplateView.as_view(template_name="core/select_recipe.html")),
        name="recipe",
    ),
    path(
        "recipes/<slug:slug>",
        profile_required(views.RecipeEditView.as_view()),
        name="recipe-edit",
    ),
    path(
        "settings/",
        TemplateView.as_view(template_name="core/settings.html"),
        name="settings",
    ),
    path(
        "profile_information/",
        login_required(views.ProfileView.as_view()),
        name="profile-information",
    ),
    path(
        "settings/profile/",
        login_required(
            TemplateView.as_view(template_name="core/profile_settings.html")
        ),
        name="profile-settings",
    ),
    path(
        "settings/profile/weight_measurements",
        profile_required(
            TemplateView.as_view(template_name="core/weight_measurements.html")
        ),
        name="profile-weight-measurements",
    ),
    path(
        "settings/account",
        login_required(
            TemplateView.as_view(template_name="core/account_settings.html")
        ),
        name="account-settings",
    ),
]
