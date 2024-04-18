"""API views associated with the `Meal` model."""
from main import models, serializers
from main.permissions import HasProfilePermission
from main.renderers import BrowsableAPIRenderer
from main.views.api.api_views import IngredientPreviewView
from main.views.api.base_views import ComponentCollectionViewSet, NutrientIntakeView
from main.views.generics import ModelViewSet
from main.views.mixins import MealInteractionMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.reverse import reverse

__all__ = (
    "MealViewSet",
    "MealIngredientViewSet",
    "MealRecipeViewSet",
    "MealNutrientIntakeView",
    "MealIngredientPreviewView",
    "MealRecipePreviewView",
)

from main.views.session_util import get_current_meal_id


class MealIngredientViewSet(MealInteractionMixin, ComponentCollectionViewSet):
    """
    List a meal's ingredients and add ingredients to a meal.

    Retrieve, update or destroy meal ingredient entry.
    """

    collection_model = models.Meal
    component_field_name = "ingredients"
    htmx_events = ["mealComponentsChanged"]
    serializer_class = serializers.MealIngredientSerializer
    detail_serializer_class = serializers.MealIngredientDetailSerializer


class MealRecipeViewSet(ComponentCollectionViewSet):
    """
    List a meal's recipes and add recipes to a meal.

    Retrieve, update or destroy meal recipe entry.
    """

    collection_model = models.Meal
    component_field_name = "recipes"
    htmx_events = ["mealComponentsChanged"]
    serializer_class = serializers.MealRecipeSerializer
    detail_serializer_class = serializers.MealRecipeDetailSerializer


class MealNutrientIntakeView(NutrientIntakeView):
    """List dietary intakes from the meal."""

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


class MealViewSet(ModelViewSet):
    """Perform CRUD operations on meals.

    Only meals owned by the user are accessible.
    """

    serializer_class = serializers.MealSerializer
    detail_serializer_class = serializers.MealDetailSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    # Unowned objects are hidden through queryset filtering,
    # so IsOwnerPermission isn't necessary
    permission_classes = [HasProfilePermission]

    # docstr-coverage: inherited
    def get_queryset(self):
        profile = self.request.user.profile
        return models.Meal.objects.filter(owner=profile).order_by("date")

    # docstr-coverage; inherited
    def perform_create(self, serializer):
        profile = self.request.user.profile
        serializer.save(owner=profile)
