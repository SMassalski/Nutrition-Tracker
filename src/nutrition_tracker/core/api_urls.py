"""Main app API URL Configuration"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns

from .routers import ModelCollectionRouter
from .views import api as views

urlpatterns = [
    path("", views.api_root, name="api-root"),
    # Nutrients
    path("nutrients/", views.NutrientView.as_view(), name="nutrient-list"),
    path(
        "nutrients/<int:pk>", views.NutrientDetailView.as_view(), name="nutrient-detail"
    ),
    path(
        "nutrients/<int:pk>/intakes",
        views.LastMonthIntakeView.as_view(),
        name="last-month-intake",
    ),
    # Ingredients
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
        "ingredients/<int:pk>/recipe-preview",
        views.IngredientPreviewView.as_view(),
        name="recipe-ingredient-preview",
    ),
    # Meal
    path(
        "profile/meals/current-meal",
        login_required(views.CurrentMealView.as_view()),
        name="current-meal",
    ),
    path(
        "profile/meals/current/ingredients",
        login_required(
            views.CurrentMealRedirectView.as_view(pattern_name="meal-ingredient-list")
        ),
        name="current-meal-ingredients",
    ),
    path(
        "profile/meals/current/recipes",
        login_required(
            views.CurrentMealRedirectView.as_view(pattern_name="meal-recipe-list")
        ),
        name="current-meal-recipes",
    ),
    path(
        "profile/meals/<int:meal>/intakes",
        login_required(views.MealNutrientIntakeView.as_view()),
        name="meal-intakes",
    ),
    path(
        "profile/meals/current/intakes",
        login_required(
            views.CurrentMealRedirectView.as_view(pattern_name="meal-intakes")
        ),
        name="current-meal-intakes",
    ),
    # Recipes
    path(
        "profile/recipes/<int:recipe>/intakes",
        views.RecipeIntakeView.as_view(),
        name="recipe-intakes",
    ),
    path(
        "profile/recipes/<int:pk>/meal-preview",
        views.MealRecipePreviewView.as_view(),
        name="meal-recipe-preview",
    ),
    # Profile
    path("profile/", views.ProfileApiView.as_view(), name="profile"),
    path(
        "profile/last-month-calories",
        views.LastMonthCalorieView.as_view(),
        name="last-month-calories",
    ),
    path(
        "profile/malconsumptions",
        views.MalconsumptionView.as_view(),
        name="malconsumptions",
    ),
    # Misc
    path(
        "add-meal-component/tabs",
        views.MealComponentTabView.as_view(),
        name="add-meal-component-tabs",
    ),
]

# Standard ViewSets
router = SimpleRouter()
router.register("profile/meals", views.MealViewSet, "meal")
router.register("profile/recipes", views.RecipeViewSet, "recipe")
router.register(
    "profile/weight-measurements", views.WeightMeasurementViewSet, "weight-measurement"
)
router.register(
    "profile/tracked-nutrients", views.TrackedNutrientViewSet, "tracked-nutrient"
)
urlpatterns += router.urls

# Component Collection ViewSets
collection_router = ModelCollectionRouter()
collection_router.register(
    "profile/meals", views.MealIngredientViewSet, "meal-ingredient"
)
collection_router.register(
    "profile/recipes",
    views.RecipeIngredientViewSet,
    "recipe-ingredient",
)
collection_router.register("profile/meals", views.MealRecipeViewSet, "meal-recipe")
urlpatterns += collection_router.urls

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "html", "api"])
