"""Serializers related to the `Meal` and `Recipe` models."""
from main import models
from rest_framework import serializers

from .fields import OwnedPrimaryKeyField

__all__ = (
    "CurrentMealSerializer",
    "MealSerializer",
    "MealDetailSerializer",
    "MealIngredientSerializer",
    "MealIngredientDetailSerializer",
    "MealRecipeSerializer",
    "MealRecipeDetailSerializer",
)


class CurrentMealSerializer(serializers.ModelSerializer):
    """Meal model's serializer for displaying and creating by dates.

    Creating using the save method requires providing the owner as an argument.
    The create method was modified to use get_or_create().
    """

    date = serializers.DateField(required=True)

    class Meta:
        model = models.Meal
        fields = ["id", "date"]

    # docstr-coverage: inherited
    def create(self, validated_data):
        instance, _ = self.Meta.model._default_manager.get_or_create(**validated_data)
        return instance


class MealIngredientSerializer(serializers.ModelSerializer):
    """MealIngredient model serializer.

    When creating an entry, the meal_id must be provided in the
    save method.
    """

    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="meal-ingredient-detail", read_only=True
    )

    class Meta:
        model = models.MealIngredient
        fields = ("url", "ingredient", "ingredient_name", "amount")


class MealIngredientDetailSerializer(MealIngredientSerializer):
    """Detail serializer for the `MealIngredient` model."""

    meal_url = serializers.HyperlinkedRelatedField(
        source="meal", view_name="meal-detail", read_only=True
    )
    ingredient_url = serializers.HyperlinkedRelatedField(
        source="ingredient", view_name="ingredient-detail", read_only=True
    )
    meal = OwnedPrimaryKeyField(queryset=models.Meal.objects.all())

    class Meta:
        model = models.MealIngredient
        fields = (
            "id",
            "meal_url",
            "meal",
            "ingredient_url",
            "ingredient",
            "ingredient_name",
            "amount",
        )


class MealRecipeSerializer(serializers.ModelSerializer):
    """`MealRecipe` model serializer.

    When creating an entry, the meal_id must be provided in the save
    method.
    """

    recipe_name = serializers.CharField(source="recipe.name", read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="meal-recipe-detail")

    class Meta:
        model = models.MealRecipe
        fields = ("url", "recipe", "recipe_name", "amount")


class MealRecipeDetailSerializer(MealRecipeSerializer):
    """Detail serializer for the `MealRecipe` model."""

    meal_url = serializers.HyperlinkedRelatedField(
        source="meal", view_name="meal-detail", read_only=True
    )
    recipe_url = serializers.HyperlinkedRelatedField(
        source="recipe", view_name="recipe-detail", read_only=True
    )
    meal = OwnedPrimaryKeyField(queryset=models.Meal.objects.all())
    recipe = OwnedPrimaryKeyField(queryset=models.Recipe.objects.all())

    class Meta:
        model = models.MealRecipe
        fields = (
            "id",
            "meal_url",
            "meal",
            "recipe_url",
            "recipe",
            "recipe_name",
            "amount",
        )


class MealSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the Meal model."""

    class Meta:
        model = models.Meal
        fields = ["url", "date"]


class MealDetailSerializer(MealSerializer):
    """Detail serializer for the Meal model."""

    ingredients = serializers.HyperlinkedIdentityField(
        "meal-ingredient-list", lookup_url_kwarg="meal"
    )
    recipes = serializers.HyperlinkedIdentityField(
        "meal-recipe-list", lookup_url_kwarg="meal"
    )
    intakes = serializers.HyperlinkedIdentityField(
        "meal-intakes", lookup_url_kwarg="meal"
    )

    class Meta:
        model = models.Meal
        fields = ["id", "date", "ingredients", "recipes", "intakes"]
