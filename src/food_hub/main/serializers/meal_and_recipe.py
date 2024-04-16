"""Serializers related to the `Meal` and `Recipe` models."""
from main import models
from rest_framework import serializers

__all__ = (
    "CurrentMealSerializer",
    "MealSerializer",
    "MealDetailSerializer",
    "MealIngredientSerializer",
    "MealIngredientDetailSerializer",
    "MealRecipeSerializer",
    "MealRecipeDetailSerializer",
    "RecipeSerializer",
    "RecipeDetailSerializer",
    "RecipeIngredientSerializer",
    "RecipeIngredientDetailSerializer",
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

    class Meta:
        model = models.MealIngredient
        fields = (
            "id",
            "meal_url",
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

    class Meta:
        model = models.MealRecipe
        fields = ("id", "meal_url", "recipe_url", "recipe", "recipe_name", "amount")


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for the RecipeIngredient model.

    When creating an entry, the recipe_id must be provided in the
    save method.
    """

    url = serializers.HyperlinkedIdentityField(
        view_name="recipe-ingredient-detail", read_only=True
    )
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = models.RecipeIngredient
        fields = ("url", "ingredient", "ingredient_name", "amount")


class RecipeIngredientDetailSerializer(RecipeIngredientSerializer):
    """Detail serializer for the RecipeIngredient model."""

    ingredient_url = serializers.HyperlinkedRelatedField(
        source="ingredient", view_name="ingredient-detail", read_only=True
    )
    recipe_url = serializers.HyperlinkedRelatedField(
        source="recipe", view_name="recipe-detail", read_only=True
    )

    class Meta:
        model = models.RecipeIngredient
        fields = (
            "id",
            "recipe_url",
            "ingredient",
            "ingredient_url",
            "ingredient_name",
            "amount",
        )


class RecipeSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the `Recipe` model."""

    slug = serializers.ReadOnlyField()

    class Meta:
        model = models.Recipe
        fields = ["url", "name", "final_weight", "slug"]

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


class RecipeDetailSerializer(RecipeSerializer):
    """Detail serializer for the recipe model."""

    ingredients = serializers.HyperlinkedIdentityField(
        "recipe-ingredient-list", lookup_url_kwarg="recipe"
    )
    intakes = serializers.HyperlinkedIdentityField(
        "recipe-intakes", lookup_url_kwarg="recipe"
    )

    class Meta:
        model = models.Recipe
        fields = ["id", "name", "final_weight", "slug", "intakes", "ingredients"]
