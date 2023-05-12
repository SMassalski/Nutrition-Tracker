"""main app's serializers"""
from rest_framework import serializers

from .models.foods import Ingredient, IngredientNutrient, Nutrient


class NutrientSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for nutrient list view."""

    class Meta:
        model = Nutrient
        fields = ["url", "name"]


class NutrientDetailSerializer(serializers.ModelSerializer):
    """Serializer for nutrient detail view."""

    class Meta:
        model = Nutrient
        fields = ["name", "unit"]


class IngredientNutrientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Ingredient - Nutrient relation from the
    Ingredient side.
    """

    url = serializers.HyperlinkedRelatedField(
        view_name="nutrient-detail", read_only=True, source="nutrient"
    )
    nutrient = NutrientDetailSerializer()

    class Meta:
        model = IngredientNutrient
        fields = ["url", "nutrient", "amount"]


class IngredientSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for ingredient list view."""

    class Meta:
        model = Ingredient
        fields = ["id", "url", "name"]


class IngredientDetailSerializer(serializers.ModelSerializer):
    """Serializer for ingredient detail view."""

    nutrients = IngredientNutrientSerializer(many=True, source="ingredientnutrient_set")

    class Meta:
        model = Ingredient
        fields = ["external_id", "name", "dataset", "nutrients"]


class IngredientPreviewSerializer(serializers.ModelSerializer):
    """Serializer for previewing ingredients."""

    macronutrients = serializers.ReadOnlyField(source="macronutrient_calories")

    class Meta:
        model = Ingredient
        fields = ["id", "name", "macronutrients"]
