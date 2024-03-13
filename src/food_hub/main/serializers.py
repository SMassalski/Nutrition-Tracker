"""Main app's serializers"""
from datetime import timedelta
from typing import Dict

from django.db.models import Q
from main import models
from rest_framework import serializers
from util import pounds_to_kilograms


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


class MealRecipeSerializer(serializers.ModelSerializer):
    """MealIngredient model serializer.

    When creating an entry, the meal_id must be provided in the save
    method.
    """

    class Meta:
        model = models.MealRecipe
        fields = ("id", "recipe", "amount")


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
