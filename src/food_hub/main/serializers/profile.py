"""Serializers related to the `Profile` model."""
from django.db.models import Q
from main import models
from rest_framework import serializers
from util import pounds_to_kilograms

__all__ = (
    "ProfileSerializer",
    "TrackedNutrientSerializer",
    "WeightMeasurementSerializer",
)


class WeightMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for the `WeightMeasurement` model.

    The 'request' needs to be included in the context for validation and
    entry creation.
    """

    POUNDS = "LBS"
    KILOGRAMS = "KG"
    unit_choices = [(POUNDS, "lbs"), (KILOGRAMS, "kg")]

    url = serializers.HyperlinkedIdentityField(view_name="weight-measurement-detail")
    unit = serializers.ChoiceField(
        choices=unit_choices, write_only=True, required=False
    )

    class Meta:
        model = models.WeightMeasurement
        fields = ("id", "url", "time", "value", "unit")

    # docstr-coverage: inherited
    def create(self, validated_data):
        validated_data["profile"] = self.context["request"].user.profile
        return models.WeightMeasurement.objects.create(**validated_data)

    # docstr-coverage: inherited
    def validate_time(self, value):
        profile = self.context["request"].user.profile
        queryset = models.WeightMeasurement.objects.filter(profile=profile, time=value)

        # On update check only entries other than that of `instance`.
        if self.instance is not None:
            queryset = queryset.filter(~Q(id=self.instance.id))

        if queryset.exists():
            raise serializers.ValidationError(
                "Weight measurement for the specified time already exists."
            )

        return value

    # docstr-coverage: inherited
    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        # Unit conversion
        unit = ret.get("unit")
        if unit == WeightMeasurementSerializer.POUNDS:
            ret["value"] = pounds_to_kilograms(ret["value"])

        ret.pop("unit", None)  # To avoid unexpected keyword arg error when saving.

        return ret


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the `Profile` model."""

    POUNDS = "LBS"
    KILOGRAMS = "KG"
    unit_choices = [(POUNDS, "lbs"), (KILOGRAMS, "kg")]
    weight_unit = serializers.ChoiceField(
        choices=unit_choices, write_only=True, required=False
    )

    # DRF does not apply min value validators to PositiveIntegerFields.
    age = serializers.IntegerField(min_value=0)
    height = serializers.IntegerField(min_value=0)
    weight = serializers.IntegerField(min_value=0)

    class Meta:
        model = models.Profile
        fields = (
            "id",
            "age",
            "height",
            "weight",
            "weight_unit",
            "activity_level",
            "sex",
        )

    # docstr-coverage: inherited
    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        # Unit conversion
        unit = ret.get("weight_unit")
        if "weight" in ret and unit == WeightMeasurementSerializer.POUNDS:
            ret["weight"] = pounds_to_kilograms(ret["weight"])

        # To avoid unexpected keyword arg error when saving.
        ret.pop("weight_unit", None)
        return ret


class TrackedNutrientSerializer(serializers.ModelSerializer):
    """Serializer for the `Profile.tracked_nutrients` through model.

    Uses the request in the context during validation.
    When saving a profile needs to be provided.
    """

    nutrient_name = serializers.CharField(source="nutrient.name", read_only=True)

    class Meta:
        model = models.Profile.tracked_nutrients.through
        fields = ["id", "nutrient", "nutrient_name"]

    # docstr-coverage: inherited
    def validate_nutrient(self, value):

        profile = self.context["request"].user.profile
        queryset = models.Profile.tracked_nutrients.through.objects.filter(
            profile=profile, nutrient=value
        )

        # On update check only entries other than that of `instance`.
        if self.instance is not None:
            queryset = queryset.filter(~Q(id=self.instance.id))

        if queryset.exists():
            raise serializers.ValidationError(
                "Nutrient is already tracked by the profile."
            )

        return value
