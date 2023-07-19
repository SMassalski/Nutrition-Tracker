"""Main app API URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import api as views
from .views import htmx

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("ingredients/", views.IngredientView.as_view(), name="ingredient-list"),
    path(
        "ingredients/<int:pk>",
        views.IngredientDetailView.as_view(),
        name="ingredient-detail",
    ),
    path(
        "ingredients/<int:pk>/preview",
        htmx.IngredientPreviewView.as_view(),
        name="ingredient-preview",
    ),
    path("nutrients/", views.NutrientView.as_view(), name="nutrient-list"),
    path(
        "nutrients/<int:pk>", views.NutrientDetailView.as_view(), name="nutrient-detail"
    ),
    # Meal and meal ingredients
    path(
        "meals/current-meal",
        login_required(htmx.CurrentMealView.as_view()),
        name="current-meal",
    ),
    path(
        "meals/<int:meal_id>/ingredients",
        login_required(htmx.MealIngredientView.as_view()),
        name="meal-ingredients",
    ),
    path(
        "meals/current/ingredients",
        login_required(
            htmx.CurrentMealRedirectView.as_view(pattern_name="meal-ingredients")
        ),
        name="current-meal-ingredients",
    ),
    path(
        "meals/ingredients/<int:pk>",
        login_required(htmx.MealIngredientDetailView.as_view()),
        name="meal-ingredient-detail",
    ),
    path(
        "meals/<int:meal_id>/intakes",
        login_required(htmx.MealNutrientIntakeView.as_view()),
        name="meal-intakes",
    ),
    path(
        "meals/current/intakes",
        login_required(
            htmx.CurrentMealRedirectView.as_view(pattern_name="meal-intakes")
        ),
        name="current-meal-intakes",
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "html", "api"])
