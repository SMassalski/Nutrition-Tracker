"""main app's serializers"""
from rest_framework import serializers

from .models import Ingredient, IngredientNutrient, Nutrient


class NutrientSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for nutrient list view"""

    # docstr-coverage: inherited
    class Meta:
        model = Nutrient
        fields = ["url", "name"]


class NutrientDetailSerializer(serializers.ModelSerializer):
    """Serializer for nutrient detail view"""

    # docstr-coverage: inherited
    class Meta:
        model = Nutrient
        fields = ["fdc_id", "name", "unit"]


class IngredientNutrientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Ingredient - Nutrient relation from the
    Ingredient side
    """

    url = serializers.HyperlinkedRelatedField(
        view_name="nutrient-detail", read_only=True, source="nutrient"
    )
    nutrient = NutrientDetailSerializer()

    # docstr-coverage: inherited
    class Meta:
        model = IngredientNutrient
        fields = ["url", "nutrient", "amount"]


class IngredientSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for ingredient list view"""

    # docstr-coverage: inherited
    class Meta:
        model = Ingredient
        fields = ["url", "name"]


class IngredientDetailSerializer(serializers.ModelSerializer):
    """Serializer for ingredient detail view"""

    nutrients = IngredientNutrientSerializer(many=True)

    # docstr-coverage: inherited
    class Meta:
        model = Ingredient
        fields = ["fdc_id", "name", "dataset", "nutrients"]
