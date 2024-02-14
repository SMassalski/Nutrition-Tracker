"""Tests of main app's serializers"""
import datetime

import pytest
from django.db import IntegrityError
from django.http import HttpRequest
from main import models, serializers
from rest_framework.reverse import reverse


@pytest.fixture
def ingredient_nutrient_1_1(ingredient_nutrient_1_1) -> models.IngredientNutrient:
    """
    IngredientNutrient associating nutrient_1 with ingredient_1.

    amount: 0.015
    """
    ingredient_nutrient_1_1.amount = 0.015
    ingredient_nutrient_1_1.save()
    return ingredient_nutrient_1_1


@pytest.fixture
def context(rf, user, saved_profile):
    """Default context for a serializer.

    Includes a request authenticated by a user with a profile
    (saved_profile fixture).
    """
    request = rf.get("")
    request.user = user
    return {"request": request}


class TestMealIngredientSerializer:
    """Tests of the MealIngredientSerializer class."""

    def test_creates_entry_using_meal_from_context(self, meal, ingredient_1):
        """
        The serializer creates the entry using the meal id passed to its
        context.
        """
        data = {"ingredient": ingredient_1.id, "amount": 3}
        serializer = serializers.MealIngredientSerializer(
            data=data, context=dict(meal=meal.id)
        )
        serializer.is_valid()

        instance = serializer.save()

        assert instance.meal == meal

    def test_raises_error_if_creating_with_missing_context(self, ingredient_1):
        data = {"ingredient": ingredient_1.id, "amount": 1}
        serializer = serializers.MealIngredientSerializer(data=data)
        serializer.is_valid()

        with pytest.raises(serializers.MissingContextError):
            serializer.save()


@pytest.fixture
def no_meal_context(saved_profile):
    """
    A serializer context for tests where the meal is not provided.

    The context contains a Request instance authenticated by a user
    with a profile.
    """
    request = HttpRequest()
    request.user = saved_profile.user
    return {"request": request}


class TestRecommendationSerializer:
    @pytest.fixture(autouse=True)
    def _serializer_kwargs(self, meal):
        """
        Default keyword arguments used for serializer construction.
        """
        self.init_kwargs = {
            "context": {"meal": meal},
        }

    @pytest.mark.parametrize(
        ("dri_type", "expected"),
        [
            (models.IntakeRecommendation.AI, 5),
            (models.IntakeRecommendation.AIK, 11.555),  # energy: 2311
            (models.IntakeRecommendation.AIKG, 400),
            (models.IntakeRecommendation.AMDR, 11.555),
            (models.IntakeRecommendation.RDA, 5),
            (models.IntakeRecommendation.RDAKG, 400),
        ],
    )
    def test_amount(
        self,
        recommendation,
        nutrient_1_energy,
        dri_type,
        expected,
    ):
        """
        The serializer's amount field returns the amount_min
        value of the recommendation adjusted for the profile attributes
        (for recommendations with `dri_type`s other than 'UL' and
        'ALAP').
        """
        recommendation.dri_type = dri_type

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("amount") == expected

    def test_amount_ul(self, recommendation):
        """
        The serializer's amount field returns the `amount_max`
        value of the recommendation adjusted for the profile attributes
        for recommendations with `dri_type` 'UL'.
        """
        recommendation.dri_type = models.IntakeRecommendation.UL

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("amount") == 5

    def test_amount_alap(self, recommendation):
        """
        The serializer's amount field returns None for
        recommendations with `dri_type` 'ALAP'.
        """
        recommendation.dri_type = models.IntakeRecommendation.ALAP

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("amount") is None

    def test_intake(self, recommendation, meal_ingredient, ingredient_nutrient_1_1):
        """
        The serializer's intake returns the amount of a nutrient in
        the meal from the `meal` context kwarg.
        """
        # meal_ingredient amount = 200 (g)
        # ingredient_nutrient_1_1 amount = 0.015
        expected = 3

        # self.init_kwargs contains the context
        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("intake") == expected

    def test_intake_missing(self, recommendation):
        """
        The serializer's intake returns 0 if the meal doesn't
        contain the recommendation's nutrient.
        """
        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("intake") == 0

    def test_intake_none(self, recommendation, no_meal_context):
        """
        The serializer's intake field returns `None` if there was no
        meal in the serializer's context.
        """
        serializer = serializers.RecommendationSerializer(
            recommendation, context=no_meal_context
        )

        assert serializer.data.get("intake") is None

    def test_over_limit_true(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's over_limit field returns the `True` if the
        intake of a nutrient is higher than the `profile_amount_max`
        of the recommendation.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 0.025
        # intake = 3
        # profile_amount_max = 2

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("over_limit")

    def test_over_limit_equal(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's over_limit field returns the `True` if the
        intake of a nutrient is equal to the `profile_amount_max`
        of the recommendation.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 0.0375
        # intake = 3
        # profile_amount_max = 3

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("over_limit")

    def test_over_limit_false(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's over_limit field returns the `False` if the
        intake of a nutrient is lower than the `profile_amount_max`
        of the recommendation.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 0.05
        # intake = 3
        # profile_amount_max = 4

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert not serializer.data.get("over_limit")

    def test_over_limit_amount_max_none(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's over_limit field returns the `False` if the
        `profile_amount_max` of the recommendation is `None`.
        """
        recommendation.amount_max = None

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert not serializer.data.get("over_limit")

    def test_over_limit_missing_intake(self, recommendation, no_meal_context):
        """
        The serializer's over_limit field returns the `False`
        if the serializer context doesn't contain a `meal`.
        """
        serializer = serializers.RecommendationSerializer(
            recommendation, context=no_meal_context
        )

        over_limit = serializer.data.get("over_limit")

        assert not over_limit

    def test_progress(self, recommendation, meal_ingredient, ingredient_nutrient_1_1):
        """
        The serializer's progress field returns the nutrient intake to
        its recommended intake as a percentage.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_min = 0.075
        # intake = 3
        # profile_amount_min = 6

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("progress") == 50

    def test_progress_100_cap(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's progress field returns 100 if the intake is
        higher than 100% of the recommendation.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_min = 0.025
        # intake = 3
        # profile_amount_min = 2

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("progress") == 100

    def test_progress_rounds(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's progress field return value is rounded to a
        whole number.
        """
        recommendation.amount_min = 9
        # intake = 3

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("progress") == 33

    def test_progress_none_target(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's progress field returns `None` if
        the value of `profile_amount_min` is `None`.
        """
        recommendation.amount_min = None

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("progress") is None

    def test_progress_zero_target(
        self, recommendation, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer's progress field returns `None` if
        the value of `profile_amount_min` is 0.
        """
        recommendation.amount_min = 0

        serializer = serializers.RecommendationSerializer(
            recommendation, **self.init_kwargs
        )

        assert serializer.data.get("progress") is None

    def test_progress_none_intake(self, recommendation, no_meal_context):
        """
        The serializer's progress field returns `None` if
        the `meal` was not provided in the context.
        """
        serializer = serializers.RecommendationSerializer(
            recommendation, context=no_meal_context
        )

        progress = serializer.data.get("progress")

        assert progress is None

    def test_no_meal_context_profile(
        self, saved_profile, recommendation, no_meal_context
    ):
        """
        When no meal is provided in the context, the serializer uses
        the profile from the request in the context.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        serializer = serializers.RecommendationSerializer(
            recommendation, context=no_meal_context
        )
        expected = 5 * 80  # recommendation amount_min * profile weight

        amount = serializer.data["amount"]

        assert amount == expected

    def test_no_profile_in_context(self, recommendation):
        """
        RecommendationSerializer.to_representation() raises an error if
        the context contains neither a `meal` nor an authenticated
        request.
        """
        serializer = serializers.RecommendationSerializer(recommendation)

        with pytest.raises(serializers.MissingContextError):
            _ = serializer.data

    def test_representation_no_meal_and_unauthenticated(self, recommendation):
        """
        RecommendationSerializer.to_representation() raises an exception
        if there is no meal in the context and the provided request
        is unauthenticated.
        """
        context = dict(request=HttpRequest())
        serializer = serializers.RecommendationSerializer(
            recommendation, context=context
        )

        with pytest.raises(serializers.MissingContextError):
            _ = serializer.data


class TestRecommendationListSerializer:
    """Tests of the RecommendationSerializer's list serializer."""

    def test_representation_profile_from_request(self, recommendation, no_meal_context):
        """
        The serializer uses the profile from the request
        if a meal wasn't provided in the context.
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.save()
        queryset = models.IntakeRecommendation.objects.all()
        expected_amount = 400
        serializer = serializers.RecommendationSerializer(
            queryset, many=True, context=no_meal_context
        )

        result = serializer.data[0]["amount"]

        assert result == expected_amount

    def test_representation_missing_profile(self):
        """
        RecommendationSerializer.to_representation() raises an exception
        if a profile cannot be retrieved from the context.
        """
        queryset = models.IntakeRecommendation.objects.all()
        serializer = serializers.RecommendationSerializer(queryset, many=True)

        with pytest.raises(serializers.MissingContextError):
            _ = serializer.data

    def test_representation_no_meal_and_unauthenticated(self):
        """
        RecommendationSerializer.to_representation() raises an exception
        if there is no meal in the context and the provided request
        is unauthenticated.
        """
        queryset = models.IntakeRecommendation.objects.all()
        context = dict(request=HttpRequest())
        serializer = serializers.RecommendationSerializer(
            queryset, many=True, context=context
        )

        with pytest.raises(serializers.MissingContextError):
            _ = serializer.data


class TestNutrientIntakeSerializer:
    """Tests of the NutrientIntakeSerializer class."""

    @pytest.fixture(autouse=True)
    def serializer_kwargs(self, meal):
        """
        Default keyword arguments used for serializer construction.
        """
        self.init_kwargs = {
            "context": {"meal": meal},
        }

    def test_nested_recommendation_meal_context(
        self, recommendation, nutrient_1, meal_ingredient, ingredient_nutrient_1_1
    ):
        """
        The serializer uses the meal from its context in the nested
        RecommendationSerializer.
        """
        recommendation.save()
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["recommendations"][0]["intake"] == 3

    def test_unit_uses_pretty_unit(self, nutrient_1):
        """
        The unit field returns the nutrient's unit symbol
        """
        nutrient_1.unit = "UG"
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["unit"] == "µg"

    def test_energy(self, nutrient_1, nutrient_1_energy):
        """
        The energy field returns the kcal/unit amount of the nutrient.
        """
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["energy"] == 10


class TestNutrientIntakeListSerializer:
    """Tests of the NutrientIntakeSerializer's list serializer class."""

    @pytest.fixture(autouse=True)
    def serializer_kwargs(self, meal):
        """
        Default keyword arguments used for serializer construction.
        """
        self.init_kwargs = {
            "context": {
                "meal": meal,
                "display_order": ["nutrient_type"],
            },
            "many": True,
        }

    def test_lists_children_representations(
        self, nutrient_1_with_type, nutrient_2_with_type, nutrient_1_child_type
    ):
        """
        If a nutrient has a child type, the representations
        of the nutrients with that type are listed under the `children`
        key.
        """
        queryset = models.Nutrient.objects.all()

        serializer = serializers.NutrientIntakeSerializer(queryset, **self.init_kwargs)

        result = serializer.data[0]["nutrients"][0]["children"][0]["id"]
        assert result == nutrient_2_with_type.id

    def test_representation_grouped_and_ordered_by_type(
        self, nutrient_1_with_type, nutrient_2_with_type
    ):
        """
        The nutrients in the representation are grouped, in the same
        order, by types listed in the `display_order` context kwarg.
        """
        self.init_kwargs["context"]["display_order"] = [
            "nutrient_type",
            "child_type",
        ]
        queryset = models.Nutrient.objects.all()

        serializer = serializers.NutrientIntakeSerializer(queryset, **self.init_kwargs)

        assert serializer.data[0]["type_name"] == "Displayed Name"
        assert serializer.data[1]["type_name"] == "Child Name"

    def test_representation_display_order_default(
        self, nutrient_1_with_type, nutrient_2_with_type
    ):
        """
        If the `display_order` context var is not provided,
        all types are displayed in alphabetic order.
        """
        queryset = models.Nutrient.objects.all()
        del self.init_kwargs["context"]["display_order"]
        serializer = serializers.NutrientIntakeSerializer(queryset, **self.init_kwargs)

        assert serializer.data[0]["type_name"] == "Child Name"
        assert serializer.data[1]["type_name"] == "Displayed Name"

    def test_representation_display_order_none(
        self, nutrient_1_with_type, nutrient_2_with_type
    ):
        """
        If the `display_order` context var is None,
        all types are displayed in alphabetic order.
        """
        queryset = models.Nutrient.objects.all()
        self.init_kwargs["context"]["display_order"] = None
        serializer = serializers.NutrientIntakeSerializer(queryset, **self.init_kwargs)

        assert serializer.data[0]["type_name"] == "Child Name"
        assert serializer.data[1]["type_name"] == "Displayed Name"

    def test_display_order_missing_type(
        self, nutrient_1_with_type, nutrient_2_with_type
    ):
        """
        The serializer does not raise a KeyError if there are no
        nutrients with a type specified in the display order.
        """
        self.init_kwargs["context"]["display_order"] = ["fake_type"]
        queryset = models.Nutrient.objects.all()

        serializer = serializers.NutrientIntakeSerializer(queryset, **self.init_kwargs)

        try:
            _ = serializer.data
        except KeyError as e:
            pytest.fail(
                f"NutrientIntakeListSerializer.to_representation() raised an error "
                f"when missing a type from display order - {e}"
            )

    def test_type_name_no_displayed_name_uses_name(
        self, nutrient_1_with_type, nutrient_type
    ):
        """
        The serializer uses the NutrientType's `name` instead of its
        `displayed_name`, if missing, for the `type_name` field.
        """
        nutrient_type.displayed_name = None
        nutrient_type.save()
        queryset = models.Nutrient.objects.all()
        serializer = serializers.NutrientIntakeSerializer(queryset, **self.init_kwargs)

        name = serializer.data[0]["type_name"]

        assert name == "nutrient_type"


class TestCurrentMealSerializer:
    def test_yesterday_field(self, meal):
        meal.date = datetime.date(2023, 6, 22)
        expected = "2023-06-21"
        serializer = serializers.CurrentMealSerializer(meal)

        assert serializer.data["yesterday"] == expected

    def test_tomorrow_field(self, meal):
        meal.date = datetime.date(2023, 6, 22)
        expected = "2023-06-23"
        serializer = serializers.CurrentMealSerializer(meal)

        assert serializer.data["tomorrow"] == expected

    def test_creates_meal_entry(self, saved_profile):
        data = {"date": "2022-06-23"}
        context = {"owner_id": saved_profile.id}
        serializer = serializers.CurrentMealSerializer(data=data, context=context)
        serializer.is_valid()

        meal = serializer.save()

        assert models.Meal.objects.filter(pk=meal.id).exists()

    def test_create_without_raising_error_if_meal_exists(self, meal):
        data = {"date": meal.date}
        context = {"owner_id": meal.owner.id}
        serializer = serializers.CurrentMealSerializer(data=data, context=context)
        serializer.is_valid()

        try:
            serializer.save()
        except IntegrityError as e:
            pytest.fail(
                f"CurrentMealSerializer caused an IntegrityError "
                f"when calling create() on duplicate meal data. - {e}"
            )

    def test_no_order_id_raises_missing_context_error(self):
        serializer = serializers.CurrentMealSerializer(data={"date": "2022-06-23"})
        serializer.is_valid()

        with pytest.raises(serializers.MissingContextError):
            serializer.save()


class TestRecipeSerializer:
    def test_creates_recipes_using_request_in_context(self, rf, saved_profile):
        request = rf.get("")
        request.user = saved_profile.user
        data = {"name": "recipe", "final_weight": 1}
        context = {"request": request}
        serializer = serializers.RecipeSerializer(data=data, context=context)
        serializer.is_valid()

        instance = serializer.save()

        assert instance.owner == saved_profile

    def test_validates_unique_together(self, recipe, rf):
        request = rf.get("")
        request.user = recipe.owner.user
        data = {"name": recipe.name, "final_weight": 1}
        context = {"request": request}
        serializer = serializers.RecipeSerializer(data=data, context=context)

        assert not serializer.is_valid()

    def test_doesnt_validate_unique_together_if_name_was_not_changed(self, recipe, rf):
        request = rf.get("")
        request.user = recipe.owner.user
        data = {"name": recipe.name, "final_weight": 1}
        context = {"request": request}
        serializer = serializers.RecipeSerializer(
            instance=recipe, data=data, context=context
        )

        assert serializer.is_valid()


class TestRecipeIngredientSerializer:
    def test_creates_using_recipe_id_in_context(self, ingredient_1, recipe):
        data = {"ingredient": ingredient_1.id, "amount": 1}
        context = {"recipe": recipe.id}
        serializer = serializers.RecipeIngredientSerializer(data=data, context=context)
        serializer.is_valid()

        instance = serializer.save()

        assert instance.recipe == recipe

    def test_raises_error_if_creating_with_missing_context(self, ingredient_1):
        data = {"ingredient": ingredient_1.id, "amount": 1}
        serializer = serializers.RecipeIngredientSerializer(data=data)
        serializer.is_valid()

        with pytest.raises(serializers.MissingContextError):
            serializer.save()


class TestMealRecipeSerializer:
    def test_creates_using_meal_id_in_context(self, recipe, meal):
        data = {"recipe": recipe.id, "amount": 1}
        context = {"meal": meal.id}
        serializer = serializers.MealRecipeSerializer(data=data, context=context)
        serializer.is_valid()

        instance = serializer.save()

        assert instance.meal == meal

    def test_raises_error_if_creating_with_missing_context(self, recipe):
        data = {"recipe": recipe.id, "amount": 1}
        serializer = serializers.MealRecipeSerializer(data=data)
        serializer.is_valid()

        with pytest.raises(serializers.MissingContextError):
            serializer.save()


class TestIngredientSerializer:
    def test_get_preview_url_context_target_is_recipe(self, ingredient_1, rf):
        request = rf.get("", data={"target": "recipe"})
        context = {"request": request}
        serializer = serializers.IngredientSerializer(ingredient_1, context=context)
        expected = reverse("recipe-ingredient-preview", args=(ingredient_1.id,))

        assert serializer.data["preview_url"] == expected

    def test_get_preview_url_no_context_target(self, ingredient_1, rf):
        request = rf.get("")
        context = {"request": request}
        serializer = serializers.IngredientSerializer(ingredient_1, context=context)
        expected = reverse("meal-ingredient-preview", args=(ingredient_1.id,))

        assert serializer.data["preview_url"] == expected


class TestRecipePreviewSerializer:
    def test_calories_field_returns_calorie_percentages_for_nutrients(
        self,
        recipe,
        ingredient_1,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1,
        nutrient_2,
        nutrient_1_energy,
        recipe_ingredient,
    ):
        models.NutrientEnergy.objects.create(nutrient=nutrient_2, amount=0.5)
        expected = {nutrient_1.name: 75, nutrient_2.name: 25}

        serializer = serializers.RecipePreviewSerializer(recipe)
        assert serializer.data["calories"] == expected


class TestWeightMeasurementSerializer:
    def test_create_uses_profile_from_request_in_context(self, rf, user, saved_profile):
        request = rf.get("")
        request.user = user
        serializer = serializers.WeightMeasurementSerializer(
            data={"value": 80}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        assert instance.profile == saved_profile

    def test_create_save_method_profile_kwarg_overrides_request_profile(
        self, rf, saved_profile, new_user
    ):
        request = rf.get("")
        request.user = new_user
        serializer = serializers.WeightMeasurementSerializer(
            data={"value": 80}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(profile=saved_profile)

        assert instance.profile == saved_profile

    def test_validate_time_profile_unique_together_create(
        self, rf, saved_profile, user, weight_measurement
    ):
        request = rf.get("")
        request.user = user
        serializer = serializers.WeightMeasurementSerializer(
            data={"value": 80, "time": weight_measurement.time},
            context={"request": request},
        )

        assert not serializer.is_valid()

    def test_validate_time_profile_unique_together_checks_entries_other_than_updated(
        self, rf, saved_profile, user, weight_measurement
    ):
        request = rf.get("")
        request.user = user
        serializer = serializers.WeightMeasurementSerializer(
            weight_measurement,
            data={"value": 90, "time": weight_measurement.time},
            context={"request": request},
        )

        assert serializer.is_valid()

        new_instance = models.WeightMeasurement.objects.create(
            profile=saved_profile, value=80
        )

        serializer = serializers.WeightMeasurementSerializer(
            weight_measurement,
            data={"value": 90, "time": new_instance.time},
            context={"request": request},
        )

        assert not serializer.is_valid()

    def test_create_pound_units(self, rf, user, saved_profile):
        request = rf.get("")
        request.user = user
        serializer = serializers.WeightMeasurementSerializer(
            data={"value": 100, "unit": "LBS"}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        assert instance.value == 45

    def test_create_kilogram_units(self, rf, user, saved_profile):
        request = rf.get("")
        request.user = user
        serializer = serializers.WeightMeasurementSerializer(
            data={"value": 100, "unit": "KG"}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()

        assert instance.value == 100


class TestProfileSerializer:
    @pytest.fixture
    def data(self):
        """Default profile data."""
        return {
            "age": 20,
            "height": 180,
            "weight": 100,
            "sex": "M",
            "activity_level": "S",
        }

    def test_create_pound_weight_units(self, user, data):
        data["weight_unit"] = "LBS"
        serializer = serializers.ProfileSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(user=user)

        assert instance.weight == 45

    def test_create_kilogram_weight_units(self, user, data):
        data["weight_unit"] = "KG"
        serializer = serializers.ProfileSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(user=user)

        assert instance.weight == 100

    def test_update_pound_weight_units(self, user, saved_profile):
        data = {"weight": 100, "weight_unit": "LBS"}
        serializer = serializers.ProfileSerializer(
            instance=saved_profile, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(user=user)

        assert instance.weight == 45

    def test_update_kilogram_weight_units(self, user, saved_profile):
        data = {"weight": 100, "weight_unit": "KG"}
        serializer = serializers.ProfileSerializer(
            instance=saved_profile, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(user=user)

        assert instance.weight == 100

    def test_update_pound_weight_units_no_weight_in_data(self, user, saved_profile):
        data = {"weight_unit": "LBS"}
        serializer = serializers.ProfileSerializer(
            instance=saved_profile, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save(user=user)

        assert instance.weight == 80  # No unit conversion, uses val from fixture.

    @pytest.mark.parametrize("field", ("age", "height", "weight"))
    def test_positive_integer_field_validation(self, field, data):
        data[field] = -1
        serializer = serializers.ProfileSerializer(data=data)

        assert not serializer.is_valid()


class TestSimpleRecommendationSerializer:
    @pytest.fixture
    def recommendation(self, recommendation):
        """An unsaved IntakeRecommendation instance.

        dri_type: "RDAKG"
        amount_min: 5.0
        amount_max: 5.0
        age_min: 0
        sex: B
        nutrient: nutrient_1
        """
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        return recommendation

    def test_get_amount_min(self, context, recommendation):
        serializer = serializers.SimpleRecommendationSerializer(
            recommendation, context=context
        )

        assert serializer.get_amount_min(recommendation) == 400

    def test_get_amount_max(self, context, recommendation):
        serializer = serializers.SimpleRecommendationSerializer(
            recommendation, context=context
        )

        assert serializer.get_amount_max(recommendation) == 400


class TestByDateIntakeSerializer:
    def test_get_intakes_date_min(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        context["date_min"] = datetime.date(2020, 6, 2)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)
        expected = 3  # from `meal`

        results = serializer.get_intakes(nutrient_1)
        assert results["Jun 15"] == expected

    def test_get_intakes_date_max(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        context["date_max"] = datetime.date(2020, 6, 2)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)
        expected = 0.3  # from `meal_2`

        results = serializer.get_intakes(nutrient_1)
        assert results["Jun 01"] == expected

    def test_get_intakes_empty_intakes_and_no_date_min_empty_results(
        self, context, nutrient_1
    ):
        context["date_max"] = datetime.date(2020, 6, 2)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        assert serializer.get_intakes(nutrient_1) == {}

    def test_get_intakes_empty_intakes_and_no_date_max_empty_results(
        self, context, nutrient_1
    ):
        context["date_min"] = datetime.date(2020, 6, 2)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        assert serializer.get_intakes(nutrient_1) == {}

    def test_get_intakes_empty_intakes(self, context, nutrient_1):
        context["date_min"] = datetime.date(2020, 6, 2)
        context["date_max"] = datetime.date(2020, 6, 10)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)
        expected = {f"Jun {2+i:02}": None for i in range(9)}

        assert serializer.get_intakes(nutrient_1) == expected

    def test_get_intakes_fills_empty_dates_with_none(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        context["date_min"] = datetime.date(2020, 6, 1)
        context["date_max"] = datetime.date(2020, 6, 10)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)
        expected = {f"Jun {2+i:02}": None for i in range(9)}

        results = serializer.get_intakes(nutrient_1)

        del results["Jun 01"]
        assert results == expected

    def test_get_intakes_values_are_rounded(
        self,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        meal_ingredient.amount = 10
        meal_ingredient.save()
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        results = serializer.get_intakes(nutrient_1)

        assert results["Jun 15"] == 0.1  # 0.15 without rounding

    def test_get_intakes_date_string_format(
        self,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        results = serializer.get_intakes(nutrient_1)

        assert "Jun 15" in results

    def test_get_intakes_results_are_sorted_chronologically(
        self,
        meal,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        context["date_min"] = datetime.date(2020, 6, 1)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)
        expected = [f"Jun {1+i:02}" for i in range(15)]

        results = serializer.get_intakes(nutrient_1)

        assert list(results.keys()) == expected

    def test_get_avg_no_intakes_doesnt_cause_division_by_zero(
        self, nutrient_1, context
    ):
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        try:
            serializer.get_avg(nutrient_1)
        except ZeroDivisionError:
            pytest.fail("ByDateIntakeSerializer.get_avg() caused a ZeroDivisionError.")

    def test_get_avg_returns_the_average_intake_of_the_nutrient(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        ingredient_nutrient_1_1.amount = 1
        ingredient_nutrient_1_1.save()
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        assert serializer.get_avg(nutrient_1) == 110

    def test_get_avg_result_is_rounded_to_first_decimal_place(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        assert serializer.get_avg(nutrient_1) == 1.6  # 1.65 without rounding

    def test_get_avg_date_min(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        context["date_min"] = datetime.date(2020, 6, 2)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        assert serializer.get_avg(nutrient_1) == 3

    def test_get_avg_date_max(
        self,
        meal,
        meal_2,
        meal_ingredient,
        ingredient_nutrient_1_1,
        nutrient_1,
        context,
    ):
        context["date_max"] = datetime.date(2020, 6, 2)
        serializer = serializers.ByDateIntakeSerializer(nutrient_1, context=context)

        assert serializer.get_avg(nutrient_1) == 0.3


class TestTrackedNutrientSerializer:
    def test_get_chart_id(self, saved_profile, nutrient_1):
        instance = models.Profile.tracked_nutrients.through.objects.create(
            profile=saved_profile, nutrient=nutrient_1
        )
        serializer = serializers.TrackedNutrientSerializer(instance)
        expected = "test-nutrient-tracked"

        actual = serializer.get_chart_id(instance)

        assert actual == expected
