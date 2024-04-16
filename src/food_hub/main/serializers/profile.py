"""Serializers related to the `Profile` model."""
from datetime import timedelta
from functools import cached_property

from django.db.models import Q
from main import models
from rest_framework import serializers
from rest_framework.reverse import reverse
from util import pounds_to_kilograms

__all__ = (
    "ProfileSerializer",
    "TrackedNutrientSerializer",
    "WeightMeasurementSerializer",
    "WeightMeasurementDetailSerializer",
    "ByDateCalorieSerializer",
)


class WeightMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for the `WeightMeasurement` model.

    When creating using the `save` method the profile must be provided
    in the args.
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
        fields = ("url", "date", "value", "unit")

    # docstr-coverage: inherited
    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        # Unit conversion
        unit = ret.get("unit")
        if unit == WeightMeasurementSerializer.POUNDS:
            ret["value"] = pounds_to_kilograms(ret["value"])

        ret.pop("unit", None)  # To avoid unexpected keyword arg error when saving.

        return ret


class WeightMeasurementDetailSerializer(WeightMeasurementSerializer):
    """Detail serializer for the WeightMeasurement model."""

    url = None

    class Meta:
        model = models.WeightMeasurement
        fields = ("id", "date", "value", "unit")


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the `Profile` model."""

    urls = [
        ("meals", "meal-list"),
        ("recipes", "recipe-list"),
        ("tracked nutrients", "tracked-nutrient-list"),
        ("last month calorie intakes", "last-month-calories"),
        ("malconsumed nutrients", "malconsumptions"),
        ("weight measurements", "weight-measurement-list"),
    ]

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

    energy_requirement = serializers.IntegerField(read_only=True)

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
            "energy_requirement",
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

    # docstr-coverage: inherited
    def to_representation(self, instance):
        ret = super().to_representation(instance)

        format_ = self.context.get("format")
        request = self.context.get("request")
        for label, view_name in self.urls:
            ret[label] = reverse(view_name, request=request, format=format_)

        return ret


class TrackedNutrientSerializer(serializers.ModelSerializer):
    """Serializer for the `Profile.tracked_nutrients` through model.

    Uses the request in the context during validation.
    When saving a profile needs to be provided.
    """

    nutrient_name = serializers.CharField(source="nutrient.name", read_only=True)
    nutrient_url = serializers.HyperlinkedRelatedField(
        source="nutrient", view_name="nutrient-detail", read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="tracked-nutrient-detail", read_only=True
    )

    class Meta:
        model = models.Profile.tracked_nutrients.through
        fields = ["url", "nutrient", "nutrient_url", "nutrient_name"]

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


class ByDateCalorieSerializer(serializers.ModelSerializer):
    """Profile serializer that displays its caloric contributions by date.

    The `date_min` and `date_max` context vars can be provided to
    limit the date range of the intakes.
    """

    avg = serializers.SerializerMethodField()
    caloric_intake = serializers.SerializerMethodField()

    class Meta:
        model = models.Profile
        fields = ("caloric_intake", "avg")

    @cached_property
    def calories(self):
        """The profile's caloric contribution of nutrients by date."""
        date_min = self.context.get("date_min")
        date_max = self.context.get("date_max")

        return self.instance.calories_by_date(date_min, date_max)

    def get_caloric_intake(self, *_args) -> dict:
        """Get the caloric contribution of nutrients grouped by date.

        Returns
        -------
        dict:
            A dictionary in the format:
            {
                "dates": <list of dates>,
                "values": {
                    <nutrient name>: <list of caloric intake values>
                    ...
                }
            }
        """

        date_min = self.context.get("date_min")
        date_max = self.context.get("date_max")

        # Don't fill the intakes if the range cannot be determined.
        if len(self.calories) == 0 and (date_min is None or date_max is None):
            return {}

        # Fill empty dates in the date range.
        date_min = date_min or min(self.calories)
        date_max = date_max or max(self.calories)

        dates = [
            date_min + timedelta(days=i) for i in range((date_max - date_min).days + 1)
        ]
        nutrients = sorted(
            list({k for v in self.calories.values() for k in v.keys()}), reverse=True
        )  # Reverse alphabetical order

        values = {
            nutrient: [
                # Round values
                round(self.calories.get(date, {}).get(nutrient, 0), 1)
                for date in dates
            ]
            for nutrient in nutrients
        }

        return {
            # Change dates to strings in the format
            #   <Month locale's abbreviated name> <zero-padded day of the month>.
            "dates": [date.strftime("%b %d") for date in dates],
            "values": values,
        }

    def get_avg(self, *_args) -> float:
        """Get the average caloric intake."""
        daily_sums = [sum(cal.values()) for cal in self.calories.values()]
        return round(sum(daily_sums) / (len(daily_sums) or 1), 1)
