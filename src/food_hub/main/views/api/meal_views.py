"""API views associated with the `Meal` model."""
from main import models, serializers
from main.views.api.api_views import IngredientPreviewView
from main.views.api.base_views import ComponentCollectionViewSet, NutrientIntakeView
from main.views.mixins import MealInteractionMixin
from rest_framework.reverse import reverse

__all__ = (
    "MealIngredientViewSet",
    "MealRecipeViewSet",
    "MealNutrientIntakeView",
    "MealIngredientPreviewView",
    "MealRecipePreviewView",
)

from main.views.session_util import get_current_meal_id


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


class MealIngredientPreviewView(IngredientPreviewView):
    """View for displaying an ingredient's preview.

    A template response includes the id of the meal the form will add
    the ingredient to.
    """

    target_pattern = "meal-ingredient-list"
    refresh_event = "currentMealChanged"

    # docstr-coverage: inherited
    def get_template_context(self, data):
        ret = super().get_template_context(data)
        ret["refresh_event"] = self.refresh_event

        meal_id = get_current_meal_id(self.request, True)
        ret["target_url"] = (
            reverse(self.target_pattern, args=(meal_id,))
            if self.target_pattern
            else None
        )
        return ret


class MealRecipePreviewView(MealIngredientPreviewView):
    """View for displaying recipe previews in the context of a meal."""

    queryset = models.Recipe.objects.all()
    target_pattern = "meal-recipe-list"
    component_field = "recipe"
