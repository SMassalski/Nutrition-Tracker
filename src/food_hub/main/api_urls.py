"""Main app API URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns

from .routers import ModelCollectionRouter
from .views import api as views

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("ingredients/", views.IngredientView.as_view(), name="ingredient-list"),
    path(
        "ingredients/<int:pk>",
        views.IngredientDetailView.as_view(),
        name="ingredient-detail",
    ),
    path(
        "ingredients/<int:pk>/meal-preview",
        views.MealIngredientPreviewView.as_view(),
        name="meal-ingredient-preview",
    ),
    path(
        "recipes/<int:pk>/meal-preview",
        views.MealRecipePreviewView.as_view(),
        name="meal-recipe-preview",
    ),
    path(
        "ingredients/<int:pk>/recipe-preview",
        views.IngredientPreviewView.as_view(),
        name="recipe-ingredient-preview",
    ),
    path("nutrients/", views.NutrientView.as_view(), name="nutrient-list"),
    path(
        "nutrients/<int:pk>", views.NutrientDetailView.as_view(), name="nutrient-detail"
    ),
    # Meal and meal ingredients
    path(
        "meals/current-meal",
        login_required(views.CurrentMealView.as_view()),
        name="current-meal",
    ),
    path(
        "meals/current/ingredients",
        login_required(
            views.CurrentMealRedirectView.as_view(pattern_name="meal-ingredient-list")
        ),
        name="current-meal-ingredients",
    ),
    path(
        "meals/current/recipes",
        login_required(
            views.CurrentMealRedirectView.as_view(pattern_name="meal-recipe-list")
        ),
        name="current-meal-recipes",
    ),
    path(
        "meals/<int:meal>/intakes",
        login_required(views.MealNutrientIntakeView.as_view()),
        name="meal-intakes",
    ),
    path(
        "meals/current/intakes",
        login_required(
            views.CurrentMealRedirectView.as_view(pattern_name="meal-intakes")
        ),
        name="current-meal-intakes",
    ),
    path(
        "recipes/<int:recipe>/intakes",
        views.RecipeIntakeView.as_view(),
        name="recipe-intakes",
    ),
    path(
        "add-meal-component/tabs",
        views.MealComponentTabView.as_view(),
        name="add-meal-component-tabs",
    ),
    path("profile/", views.ProfileApiView.as_view(), name="profile"),
    path(
        "nutrients/<int:pk>/intakes",
        views.LastMonthIntakeView.as_view(),
        name="last-month-intake",
    ),
    path(
        "calories/last-month",
        views.LastMonthCalorieView.as_view(),
        name="last-month-calories",
    ),
    path(
        "profile/malconsumptions",
        views.MalconsumptionView.as_view(),
        name="malconsumptions",
    ),
]
router = SimpleRouter()
router.register("recipes", views.RecipeViewSet, "recipe")
router.register(
    "weight-measurements", views.WeightMeasurementViewSet, "weight-measurement"
)
router.register("tracked-nutrients", views.TrackedNutrientViewSet, "tracked-nutrient")
urlpatterns += router.urls

collection_router = ModelCollectionRouter()
collection_router.register("meal", views.MealIngredientViewSet, "meal-ingredient")
collection_router.register(
    "recipe",
    views.RecipeIngredientViewSet,
    "recipe-ingredient",
)
collection_router.register("meal", views.MealRecipeViewSet, "meal-recipe")
urlpatterns += collection_router.urls

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "html", "api"])
