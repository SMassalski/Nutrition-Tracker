"""main app API URL Configuration"""
from django.urls import path

from .views import api as views

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("ingredients/", views.IngredientView.as_view(), name="ingredient-list"),
    path(
        "ingredients/<int:pk>",
        views.IngredientDetailView.as_view(),
        name="ingredient-detail",
    ),
    path("nutrients/", views.NutrientView.as_view(), name="nutrient-list"),
    path(
        "nutrients/<int:pk>", views.NutrientDetailView.as_view(), name="nutrient-detail"
    ),
]
