"""main app's serializers"""
from datetime import timedelta

from django.db.models import Manager
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

    calories = serializers.SerializerMethodField()

    class Meta:
        model = models.Ingredient
        fields = ["id", "name", "calories"]

    def get_calories(self, obj: models.Ingredient) -> dict:
        """The percentage of energy each nutrient provides."""
        calories = obj.calories
        total = sum(calories.values())
        return {nutrient.name: val * 100 / total for nutrient, val in calories.items()}


class CurrentMealSerializer(serializers.ModelSerializer):
    """Meal model's serializer for displaying and creating by dates.

    Displays the meal's date (as a date object), and the dates of one
    day before and after (as str in iso format).

    Requires a profile id in the context.
    The create method was modified to use get_or_create().
    """

    date = serializers.DateField(required=True)
    yesterday = serializers.SerializerMethodField()
    tomorrow = serializers.SerializerMethodField()

    class Meta:
        model = models.Meal
        fields = ["id", "yesterday", "date", "tomorrow"]

    @staticmethod
    def get_yesterday(obj: models.Meal) -> str:
        """The date a day before the meal's date in iso format."""
        return str(obj.date - timedelta(days=1))

    @staticmethod
    def get_tomorrow(obj: models.Meal) -> str:
        """The date a day after the meal's date in iso format."""
        return str(obj.date + timedelta(days=1))

    # docstr-coverage: inherited
    def create(self, validated_data):
        owner_id = self.context.get("owner_id")
        if owner_id is None:
            raise MissingContextError(
                "Creating a meal using the CurrentMealSerializer requires passing the "
                "`owner_id` in the context."
            )

        validated_data["owner_id"] = owner_id
        instance, _ = self.Meta.model._default_manager.get_or_create(**validated_data)
        return instance


class MealIngredientSerializer(serializers.ModelSerializer):
    """MealIngredient model serializer."""

    ingredient_name = serializers.ReadOnlyField(source="ingredient.name")

    class Meta:
        model = models.MealIngredient
        fields = ("id", "ingredient", "amount", "ingredient_name")

    # docstr-coverage: inherited
    def create(self, validated_data):
        validated_data["meal_id"] = self.context["meal_id"]
        return super().create(validated_data)


class RecommendationListSerializer(serializers.ListSerializer):
    """A list serializer for IntakeRecommendations."""

    # docstr-coverage: inherited
    def to_representation(self, data):
        _update_context_intakes(self.context)
        profile = _get_profile_from_context(self.context)

        if profile is None:
            raise MissingContextError(
                "RecommendationSerializer requires a profile to work correctly. Add "
                "to the context either a `models.Meal` instance under the 'meal' key or"
                " an authenticated request under the 'request' key."
            )

        return super().to_representation(data)


class RecommendationSerializer(serializers.ModelSerializer):
    """A model serializer for IntakeRecommendations.

    The `intake`, `progress` and `over_limit` fields depend on
    a models.Meal instance as the `meal` context variable.
    """

    amount = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    intake = serializers.SerializerMethodField()
    over_limit = serializers.SerializerMethodField()

    class Meta:
        model = models.IntakeRecommendation
        list_serializer_class = RecommendationListSerializer
        fields = ("id", "dri_type", "intake", "amount", "progress", "over_limit")

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._profile = None
        self._intakes = {}

    # docstr-coverage: inherited
    def to_representation(self, instance):

        self._profile = _get_profile_from_context(self.context)

        if self._profile is None:
            raise MissingContextError(
                "RecommendationSerializer requires a profile to work correctly. Add "
                "to the context either a `models.Meal` instance under the 'meal' key or"
                " an authenticated request under the 'request' key."
            )
        _update_context_intakes(self.context)
        self._intakes = self.context.get("intakes")

        return super().to_representation(instance)

    def get_amount(self, obj: models.IntakeRecommendation):
        """The displayed amount for a recommendation.

        The field used differs between dri_types.
        """
        if obj.dri_type == "ALAP":
            return None
        elif obj.dri_type == "UL":
            amount = obj.profile_amount_max(self._profile)
        else:
            amount = obj.profile_amount_min(self._profile)

        return amount

    def get_progress(self, obj: models.IntakeRecommendation):
        """
        The ratio of the nutrient intake to the recommended nutrient
        intake in percent.
        """
        intake = self.get_intake(obj)
        target = obj.profile_amount_min(self._profile)

        try:
            progress = min(round(100 * intake / target), 100)
        except (TypeError, ZeroDivisionError):
            # Recommendation's amount min is 0 or the intake is None
            # because no meal was provided in the context.
            progress = None

        return progress

    def get_intake(self, obj: models.IntakeRecommendation):
        """The intake of the nutrient."""
        if self._intakes is None:
            return None
        return self._intakes.get(obj.nutrient_id, 0)

    def get_over_limit(self, obj: models.IntakeRecommendation):
        """
        Whether the nutrient's intake is higher than or equal to the
        recommended upper limit.
        """
        limit = obj.profile_amount_max(self._profile) or float("inf")
        intake = self.get_intake(obj)

        if intake is None:
            return False
        return intake >= limit


class NutrientTypeSerializer(serializers.ModelSerializer):
    """A model serializer for NutrientTypes."""

    class Meta:
        model = models.NutrientType
        fields = ("name", "displayed_name", "parent_nutrient_id")


class NutrientIntakeListSerializer(serializers.ListSerializer):
    """A list serializer for Nutrients with intake information.

    In the representation, the nutrients are grouped by NutrientTypes.
    The list serializer also adds a `children` field, which is a list
    of NutrientIntake representations that have a type with
    a `parent_nutrient` set to the current nutrient.

    Context Vars
    ------------
    display_order: Iterable[str]
        The names of types that will be represented in that order.
        Nutrients without types in `display_order` will be ignored.
        If `None`, all present types are included in alphabetical order.

    Notes
    ------
    The nested RecommendationSerializer requires a `models.Meal`
    instance ("meal" context var) to work correctly.
    Without a meal or an authenticated request in the context, the
    serializer will raise an exception.
    """

    # docstr-coverage: inherited
    def to_representation(self, data):
        _update_context_intakes(self.context)
        iterable = data.all() if isinstance(data, Manager) else data

        child_representations = [
            self.child.to_representation(item) for item in iterable
        ]
        by_type = {}
        for nutrient in child_representations:
            for type_ in nutrient["types"]:
                name, displayed_name = type_["name"], type_["displayed_name"]
                if name not in by_type:
                    by_type[name] = {
                        "type_name": displayed_name or name,
                        "nutrients": [],
                    }
                by_type[name]["nutrients"].append(nutrient)

        display_order = self.context.get("display_order") or sorted(by_type.keys())

        for nutrient in child_representations:
            if nutrient["child_type"] in by_type:
                nutrient["children"] = by_type[nutrient["child_type"]]["nutrients"]
            else:
                nutrient["children"] = []

        return [by_type[type_] for type_ in display_order if type_ in by_type]


class NutrientIntakeSerializer(serializers.ModelSerializer):
    """A model serializer for Nutrients with intake information.

    In the representation, the nutrients are grouped by NutrientTypes.
    The list serializer also adds a `children` field, which is a list
    of NutrientIntake representations that have a type with
    a `parent_nutrient` set to the current nutrient.

    Context Vars
    ------------
    display_order: Iterable[str]
        The names of types that will be represented in that order.
        Nutrients without types in `display_order` will be ignored.
        If `None`, all present types are included in alphabetical order.
        List serializer only.

    Notes
    ------
    The nested RecommendationSerializer requires a `models.Meal`
    instance ("meal" context var) to work correctly.
    Without a meal or an authenticated request in the context, the
    serializer will raise an exception.

    It is recommended to use select_related("energy", "child_type") and
    prefetch_related("types", "recommendations") to avoid n+1 queries.
    The nested IntakeRecommendations can be filtered by using
    the Prefetch object with a modified queryset.
    """

    recommendations = RecommendationSerializer(many=True)
    unit = serializers.CharField(source="pretty_unit")
    energy = serializers.FloatField(source="energy_per_unit")
    types = NutrientTypeSerializer(many=True)
    child_type = serializers.CharField(source="child_type.name")
    intake = serializers.SerializerMethodField()

    class Meta:
        list_serializer_class = NutrientIntakeListSerializer
        model = models.Nutrient
        fields = (
            "id",
            "name",
            "unit",
            "energy",
            "recommendations",
            "types",
            "child_type",
            "intake",
        )

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        self._intakes = None
        super().__init__(*args, **kwargs)

    # docstr-coverage: inherited
    def to_representation(self, instance):
        _update_context_intakes(self.context)
        self._intakes = self.context.get("intakes")
        return super().to_representation(instance)

    def get_intake(self, obj: models.Nutrient):
        """The intake of the nutrient."""
        if self._intakes is None:
            return None
        return self._intakes.get(obj.id, 0)


def _get_profile_from_context(context: dict) -> models.Profile:
    """
    Retrieve the profile from either a meal or a request in the `context`.
    """
    if "meal" in context:
        profile = context["meal"].owner
    elif "request" in context:
        try:
            profile = context["request"].user.profile
        except AttributeError:
            # Unauthenticated user
            profile = None
    else:
        profile = None

    return profile


def _update_context_intakes(context: dict) -> None:
    """Add the meal intakes to context if missing.

    Works only if a `meal` is in the context.
    This is to allow retrieving the intakes once as early in the
    serializer hierarchy as possible.
    """
    if "intakes" not in context and "meal" in context:
        context["intakes"] = context["meal"].get_intakes()


class MissingContextError(ValueError):
    """
    Raised when a required value is missing from a serializer's context.
    """
