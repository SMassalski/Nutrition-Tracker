"""
Serializers related to the `Nutrient`, `Ingredient`
and `IntakeRecommendation` models.
"""
from datetime import timedelta
from typing import Dict

from main import models
from rest_framework import serializers

__all__ = (
    "NutrientSerializer",
    "NutrientDetailSerializer",
    "IngredientNutrientSerializer",
    "IngredientSerializer",
    "IngredientDetailSerializer",
    "RecommendationSerializer",
    "NutrientTypeSerializer",
    "NutrientIntakeSerializer",
    "SimpleRecommendationSerializer",
    "ByDateIntakeSerializer",
)


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


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient list view."""

    class Meta:
        model = models.Ingredient
        fields = ["id", "name"]


class IngredientDetailSerializer(serializers.ModelSerializer):
    """Serializer for ingredient detail view."""

    nutrients = IngredientNutrientSerializer(many=True, source="ingredientnutrient_set")

    class Meta:
        model = models.Ingredient
        fields = ["external_id", "name", "dataset", "nutrients"]


class RecommendationSerializer(serializers.ModelSerializer):
    """A model serializer for IntakeRecommendations.

    Requires a request authenticated with a user with a profile in the
    context. Additionally, some fields require `intakes`
    (dict[<nutrient_id>, <intake>]) in context to work correctly.
    """

    class Meta:
        model = models.IntakeRecommendation
        fields = ("id", "dri_type", "displayed_amount", "progress", "over_limit")

    # docstr-coverage: inherited
    def to_representation(self, instance: models.IntakeRecommendation):

        profile = self.context["request"].user.profile
        intakes = self.context.get("intakes", {})
        instance.set_up(profile, intakes.get(instance.nutrient_id))

        return super().to_representation(instance)


class NutrientTypeSerializer(serializers.ModelSerializer):
    """A model serializer for NutrientTypes."""

    class Meta:
        model = models.NutrientType
        fields = ("id", "name", "displayed_name", "parent_nutrient_id")


class NutrientIntakeSerializer(serializers.ModelSerializer):
    """A model serializer for Nutrients with intake information.

    Requires a request authenticated with a user with a profile in the
    context. Additionally, some fields require `intakes`
    (dict[<nutrient_id>, <intake>]) in context to work correctly.

    It is recommended to use select_related("energy", "child_type") and
    prefetch_related("types", "recommendations") to avoid n+1 queries.
    The nested IntakeRecommendations can be filtered by using
    the Prefetch object with a modified queryset.
    """

    recommendations = RecommendationSerializer(many=True)
    types = NutrientTypeSerializer(many=True)
    intake = serializers.SerializerMethodField()

    class Meta:
        model = models.Nutrient
        fields = (
            "id",
            "name",
            "unit",
            "pretty_unit",
            "energy_per_unit",
            "recommendations",
            "types",
            "child_type",
            "intake",
        )

    def get_intake(self, obj: models.Nutrient):
        """The intake of the nutrient."""
        intakes = self.context.get("intakes")
        if intakes is None:
            return None
        return intakes.get(obj.id, 0)


class SimpleRecommendationSerializer(serializers.ModelSerializer):
    """
    A simple serializer for the IntakeRecommendation model.

    Requires a `request` in the context.
    The request must be authenticated for a user with a profile.
    """

    amount_min = serializers.SerializerMethodField()
    amount_max = serializers.SerializerMethodField()

    class Meta:
        model = models.IntakeRecommendation
        fields = ("id", "dri_type", "amount_min", "amount_max")

    def get_amount_min(self, obj: models.IntakeRecommendation) -> float:
        """Get the amount min adjusted for the profile."""
        profile = self.context["request"].user.profile
        return obj.profile_amount_min(profile)

    def get_amount_max(self, obj: models.IntakeRecommendation) -> float:
        """Get the amount min adjusted for the profile."""
        profile = self.context["request"].user.profile
        return obj.profile_amount_max(profile)


class ByDateIntakeSerializer(serializers.ModelSerializer):
    """Nutrient serializer that displays its intakes by date.

    Includes recommendations for the nutrient.

    Requires an authenticated request in the context to work correctly.
    The `date_min` and `date_max` context vars can be provided to
    limit the date range of the intakes.
    """

    intakes = serializers.SerializerMethodField()
    recommendations = SimpleRecommendationSerializer(many=True)
    unit = serializers.CharField(source="pretty_unit")
    avg = serializers.SerializerMethodField()

    class Meta:
        model = models.Nutrient
        fields = ("id", "name", "unit", "intakes", "recommendations", "avg")

    def get_intakes(self, obj: models.Nutrient) -> Dict[str, float]:
        """Get the intakes of the nutrient grouped by date.

        Requires a `request` in the context.
        The request must be authenticated for a user with a profile.

        Context Params
        --------------
        date_min: date
            The lower limit (inclusive) of dates to be included in the
            results.
        date_max: date
            The upper limit (inclusive) of dates to be included in the
            results.
        """
        profile = self.context["request"].user.profile
        date_min = self.context.get("date_min")
        date_max = self.context.get("date_max")

        intakes = profile.intakes_by_date(obj.id, date_min, date_max)

        # Don't fill the intakes if the range cannot be determined.
        if len(intakes) == 0 and (date_min is None or date_max is None):
            return {}

        # Fill empty dates in the date range.
        date_min = date_min or min(intakes)
        date_max = date_max or max(intakes)

        result = {
            date_min + timedelta(days=i): None
            for i in range((date_max - date_min).days + 1)
        }
        result.update(intakes)

        # Change dates to strings in the format
        #   <Month locale's abbreviated name> <zero-padded day of the month>.
        # Round the values to the first decimal place.
        return {
            d.strftime("%b %d"): round(result[d], 1) if result[d] is not None else None
            for d in result
        }

    def get_avg(self, obj: models.Nutrient) -> float:
        """Get the average intake of the nutrient.

        Requires a `request` in the context.
        The request must be authenticated for a user with a profile.

        Context Params
        --------------
        date_min: date
            The lower limit (inclusive) of dates to be included in the
            calculation.
        date_max: date
            The upper limit (inclusive) of dates to be included in the
            calculation.
        """
        profile = self.context["request"].user.profile
        date_min = self.context.get("date_min")
        date_max = self.context.get("date_max")
        intakes = profile.intakes_by_date(obj.id, date_min, date_max)

        return round(sum(intakes.values()) / (len(intakes) or 1), 1)