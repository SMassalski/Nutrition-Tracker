"""main app's api views"""
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.renderers import (
    BrowsableAPIRenderer,
    JSONRenderer,
    TemplateHTMLRenderer,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .. import serializers
from ..models import Ingredient, Nutrient


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


class IngredientView(GenericAPIView, ListModelMixin):
    """List of ingredients

    Include a query in the `search` query parameter to only
    list the ingredients with matching names.
    """

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, TemplateHTMLRenderer]

    # TODO: HTMX in separate views?
    def get(self, request, *args, **kwargs):
        """List ingredients.

        Search filtering enabled. HTML format returns ingredients in
        the form of table rows.
        """
        if kwargs.get("format") == "html":
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                {"ingredient_list": serializer.data},
                template_name="main/data/ingredient_names.html",
            )
        return self.list(request, *args, **kwargs)


class IngredientDetailView(RetrieveAPIView):
    """Ingredient details"""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientDetailSerializer
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, TemplateHTMLRenderer]


class IngredientPreview(GenericAPIView, RetrieveModelMixin):
    """Ingredient preview (selected ingredient information)."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientPreviewSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request, *args, **kwargs):
        """Retrieve ingredient preview in HTML format

        The preview includes a macronutrient pie chart, a description
        and an `add ingredient` form.
        """
        obj = self.get_object()
        return Response(
            {"ingredient": self.get_serializer(obj).data},
            template_name="main/data/ingredient_preview.html",
        )


class NutrientView(ListAPIView):
    """List of nutrients"""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientSerializer


class NutrientDetailView(RetrieveAPIView):
    """Nutrient detail"""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientDetailSerializer
