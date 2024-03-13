"""Tests of main app's serializers"""
import datetime

import pytest
from django.db import IntegrityError
from main import models, serializers


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


class TestNutrientIntakeSerializer:
    """Tests of the NutrientIntakeSerializer class."""

    @pytest.fixture(autouse=True)
    def serializer_kwargs(self, context):
        """
        Default keyword arguments used for serializer construction.
        """
        self.intakes = {}
        context["intakes"] = self.intakes
        self.init_kwargs = {
            "context": context,
        }

    def test_get_intakes_returns_intake_of_nutrient(self, nutrient_1):
        self.intakes[nutrient_1.id] = 5
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["intake"] == 5

    def test_get_intakes_zero_if_nutrient_not_in_intakes(self, nutrient_1):
        self.intakes = {}
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["intake"] == 0


class TestCurrentMealSerializer:
    def test_creates_meal_entry(self, saved_profile):
        data = {"date": "2022-06-23"}
        serializer = serializers.CurrentMealSerializer(data=data)
        serializer.is_valid()

        meal = serializer.save(owner=saved_profile)

        assert models.Meal.objects.filter(pk=meal.id).exists()

    def test_create_without_raising_error_if_meal_exists(self, meal, saved_profile):
        data = {"date": meal.date}
        serializer = serializers.CurrentMealSerializer(data=data)
        serializer.is_valid()

        try:
            serializer.save(owner=saved_profile)
        except IntegrityError as e:
            pytest.fail(
                f"CurrentMealSerializer caused an IntegrityError "
                f"when calling create() on duplicate meal data. - {e}"
            )


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
