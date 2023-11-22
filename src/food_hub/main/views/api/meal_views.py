"""API views associated with the `Meal` model."""
from main import models, serializers
from main.mixins import MealInteractionMixin
from main.views.api.base_views import ComponentCollectionViewSet, NutrientIntakeView

__all__ = ("MealIngredientViewSet", "MealRecipeViewSet", "MealNutrientIntakeView")


class MealIngredientViewSet(MealInteractionMixin, ComponentCollectionViewSet):
    """
    The ComponentCollectionViewSet for the Meal-Ingredient relationship.
    """

    collection_model = models.Meal
    component_field_name = "ingredients"
    htmx_events = ["mealComponentsChanged"]
    serializer_class = serializers.MealIngredientSerializer


class MealRecipeViewSet(ComponentCollectionViewSet):
    """
    The ComponentCollectionViewSet for the Meal-Recipe relationship.
    """

    collection_model = models.Meal
    component_field_name = "recipes"
    htmx_events = ["mealComponentsChanged"]
    serializer_class = serializers.MealRecipeSerializer


class MealNutrientIntakeView(NutrientIntakeView):
    """NutrientIntakeView for the meal model."""

    collection_model = models.Meal
    lookup_url_kwarg = "meal"
