"""main app's api views"""
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .. import serializers
from ..models import Ingredient, Nutrient


@api_view(["GET"])
def api_root(request):
    """Browsable API root"""
    return Response(
        {
            "Ingredients": reverse("ingredient-list", request=request),
            "Nutrients": reverse("nutrient-list", request=request),
        }
    )


class IngredientView(ListAPIView):
    """List of ingredients"""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class IngredientDetailView(RetrieveAPIView):
    """Ingredient details"""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientDetailSerializer


class NutrientView(ListAPIView):
    """List of nutrients"""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientSerializer


class NutrientDetailView(RetrieveAPIView):
    """Nutrient detail"""

    queryset = Nutrient.objects.all()
    serializer_class = serializers.NutrientDetailSerializer
