"""Serializers related to the `Recipe` model."""
from main import models
from main.serializers.fields import OwnedPrimaryKeyField
from rest_framework import serializers

__all__ = (
    "RecipeIngredientSerializer",
    "RecipeIngredientDetailSerializer",
    "RecipeSerializer",
    "RecipeDetailSerializer",
)


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
    recipe = OwnedPrimaryKeyField(queryset=models.Recipe.objects.all())

    class Meta:
        model = models.RecipeIngredient
        fields = (
            "id",
            "recipe_url",
            "recipe",
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
