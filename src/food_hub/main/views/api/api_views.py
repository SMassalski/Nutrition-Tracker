"""Main app's api views."""
from main import models, serializers
from main.models.foods import Ingredient, Nutrient
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.renderers import (
    BrowsableAPIRenderer,
    JSONRenderer,
    TemplateHTMLRenderer,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

__all__ = (
    "api_root",
    "IngredientView",
    "IngredientDetailView",
    "NutrientView",
    "NutrientDetailView",
    "IngredientPreviewView",
    "MealIngredientPreviewView",
    "MealRecipePreviewView",
)

from main.views.session_util import get_current_meal_id


# TODO: Remove unused views
@api_view(["GET"])
@renderer_classes([BrowsableAPIRenderer, JSONRenderer])
def api_root(request, format=None):
    """Browsable API root"""
    return Response(
        {
            "Ingredients": reverse("ingredient-list", request=request),
            "Nutrients": reverse("nutrient-list", request=request),
        }
    )


class IngredientView(ListAPIView):
    """List of ingredients.

    Include a query in the `search` query parameter to only
    list the ingredients with matching names.
    """

    queryset = Ingredient.objects.order_by("name")
    serializer_class = serializers.IngredientSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer]
    template_name = "main/data/component_search_result_list.html"

    def get(self, *args, **kwargs):
        """List ingredients."""
        response = super().get(*args, **kwargs)
        response.data["obj_type"] = "ingredients"
        return response


class IngredientDetailView(RetrieveAPIView):
    """Ingredient details."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientDetailSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, TemplateHTMLRenderer]


class NutrientView(ListAPIView):
    """List of nutrients."""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientSerializer


class NutrientDetailView(RetrieveAPIView):
    """Nutrient details."""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientDetailSerializer


class IngredientPreviewView(RetrieveAPIView):
    """Ingredient preview (selected ingredient information)."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientPreviewSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "main/data/preview.html"

    refresh_event = None
    component_field = "ingredient"

    def get(self, request, *args, **kwargs):
        """Retrieve ingredient preview data."""
        response = super().get(request, *args, **kwargs)

        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):

            response.data["component_field"] = self.component_field

        return response


class MealIngredientPreviewView(IngredientPreviewView):
    """View for displaying an ingredient's preview.

    A template response includes the id of the meal the form will add
    the ingredient to.
    """

    target_pattern = "meal-ingredient-list"
    refresh_event = "currentMealChanged"

    # docstr-coverage: inherited
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if isinstance(request.accepted_renderer, TemplateHTMLRenderer):
            meal_id = get_current_meal_id(self.request, True)
            response.data["target_url"] = (
                reverse(self.target_pattern, args=(meal_id,))
                if self.target_pattern
                else None
            )
            response.data["refresh_event"] = self.refresh_event

        return response


class MealRecipePreviewView(MealIngredientPreviewView):
    """View for displaying recipe previews in the context of a meal."""

    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipePreviewSerializer
    target_pattern = "meal-recipe-list"
    component_field = "recipe"
