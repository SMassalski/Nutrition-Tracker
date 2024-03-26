"""Main app's api views."""

from main import serializers
from main.models import Ingredient, Nutrient
from main.views.generics import ListAPIView, RetrieveAPIView
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.filters import SearchFilter
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
)


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

    # docstr-coverage: inherited
    def get_template_context(self, data):
        target = self.request.GET.get("target", "").lower()
        preview_url_name = (
            "recipe-ingredient-preview"
            if target == "recipe"
            else "meal-ingredient-preview"
        )
        return {"obj_type": "ingredients", "preview_url_name": preview_url_name}


class IngredientDetailView(RetrieveAPIView):
    """Ingredient details."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientDetailSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]


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
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "main/data/preview.html"

    refresh_event = None
    component_field = "ingredient"

    # docstr-coverage: inherited
    def get_template_context(self, data):

        return {
            "component_field": self.component_field,
            "calories": data["obj"].calorie_ratio,
        }
