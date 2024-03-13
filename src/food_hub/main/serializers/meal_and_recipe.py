"""Serializers related to the `Meal` and `Recipe` models."""
from main import models
from rest_framework import serializers

__all__ = (
    "CurrentMealSerializer",
    "MealIngredientSerializer",
    "MealRecipeSerializer",
    "RecipeSerializer",
    "RecipeIngredientSerializer",
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

    class Meta:
        model = models.MealIngredient
        fields = ("id", "ingredient", "amount")


class MealRecipeSerializer(serializers.ModelSerializer):
    """MealIngredient model serializer.

    When creating an entry, the meal_id must be provided in the save
    method.
    """

    class Meta:
        model = models.MealRecipe
        fields = ("id", "recipe", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the `Recipe` model."""

    slug = serializers.ReadOnlyField()

    class Meta:
        model = models.Recipe
        fields = ["id", "name", "final_weight", "slug"]

    # docstr-coverage: inherited
    def validate(self, data):
        owner = self.context["request"].user.profile.id
        # Don't check the unique together constraint if the name wasn't changed.
        if (
            self.instance
            and models.Recipe.objects.get(pk=self.instance.id).name == data["name"]
        ):
            return data
        if models.Recipe.objects.filter(owner=owner, name=data["name"]).exists():
            raise serializers.ValidationError(
                f"This profile already has a recipe with the name {data['name']}."
            )
        return data

    # docstr-coverage: inherited
    def create(self, validated_data):
        # Not enforcing the modification of preform create in views
        # because the request is also needed for validation
        validated_data["owner_id"] = self.context["request"].user.profile.id
        return super().create(validated_data)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """RecipeIngredient model serializer.

    When creating an entry, the recipe_id must be provided in the
    save method.
    """

    class Meta:
        model = models.RecipeIngredient
        fields = ("id", "ingredient", "amount")
