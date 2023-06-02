"""main app's serializers"""
from main import models
from rest_framework import serializers


class NutrientSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for nutrient list view."""

    class Meta:
        model = models.Nutrient
        fields = ["url", "name"]


class NutrientDetailSerializer(serializers.ModelSerializer):
    """Serializer for nutrient detail view."""

    class Meta:
        model = models.Nutrient
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
        model = models.IngredientNutrient
        fields = ["url", "nutrient", "amount"]


class IngredientSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for ingredient list view."""

    class Meta:
        model = models.Ingredient
        fields = ["id", "url", "name"]


class IngredientDetailSerializer(serializers.ModelSerializer):
    """Serializer for ingredient detail view."""

    nutrients = IngredientNutrientSerializer(many=True, source="ingredientnutrient_set")

    class Meta:
        model = models.Ingredient
        fields = ["external_id", "name", "dataset", "nutrients"]


class IngredientPreviewSerializer(serializers.ModelSerializer):
    """Serializer for previewing ingredients."""

    macronutrients = serializers.ReadOnlyField(source="macronutrient_calories")

    class Meta:
        model = models.Ingredient
        fields = ["id", "name", "macronutrients"]


class ProfileRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for IntakeRecommendations with Profile information.

    Adjusts amounts according to profile attributes.
    The serializer uses information from related fields. Using
    select_related("nutrient", "nutrient_energy") and
    .prefetch_related("nutrient__types") is recommended.
    """

    profile_amount_min = serializers.SerializerMethodField()
    nutrient_id = serializers.IntegerField(source="nutrient.id")
    name = serializers.CharField(source="nutrient.name")
    unit = serializers.CharField(source="nutrient.pretty_unit")
    energy = serializers.FloatField(source="nutrient.energy_per_unit")
    types = serializers.SerializerMethodField()
    upper_limit = serializers.SerializerMethodField()
    displayed_amount = serializers.SerializerMethodField()

    class Meta:
        model = models.IntakeRecommendation
        exclude = ("id", "age_min", "age_max", "sex", "nutrient")

    def get_profile_amount_min(self, obj: models.IntakeRecommendation):
        """
        The recommendations `amount_min` taking into account profile
        attributes.
        """
        return obj.profile_amount_min(self.context.get("profile"))

    def get_types(self, obj: models.IntakeRecommendation):
        """
        The NutrientTypes of the recommendation's related Nutrient.
        """
        return [(t.name, t.displayed_name) for t in obj.nutrient.types.all()]

    def get_upper_limit(self, obj: models.IntakeRecommendation) -> float:
        """The UL or AMDR upper limit of the recommendation"""
        if obj.dri_type == "UL":
            amount = obj.profile_amount_min(self.context.get("profile"))
        else:
            amount = obj.profile_amount_max(self.context.get("profile"))

        return amount or float("inf")

    def get_displayed_amount(self, obj: models.IntakeRecommendation):
        """The displayed amount for a recommendation.

        The field used differs between dri_types.
        """
        if obj.dri_type == "ALAP":
            return None

        amount = obj.profile_amount_min(self.context.get("profile"))
        return None if amount is None else round(amount, 1)
