"""Main app API URL Configuration"""
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

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
        "ingredients/<int:pk>/preview",
        views.IngredientPreview.as_view(),
        name="ingredient-preview",
    ),
    path("nutrients/", views.NutrientView.as_view(), name="nutrient-list"),
    path(
        "nutrients/<int:pk>", views.NutrientDetailView.as_view(), name="nutrient-detail"
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "html", "api"])
