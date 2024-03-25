"""Tests of profile related features."""
from datetime import date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from main import models


class TestProfile:
    """Tests of the Profile model."""

    @pytest.mark.parametrize(
        ("age", "weight", "height", "sex", "expected"),
        [
            (35, 80, 180, "M", 2819),  # Adult male
            (35, 80, 180, "F", 2414),  # Adult female
            (15, 50, 170, "M", 2428),  # Non-adult male
            (15, 50, 170, "F", 2120),  # Non-adult female
            (2, 12, 80, "M", 988),  # 2 years old
            (0, 9, 80, "F", 723),  # less than 1 year old
        ],
    )
    def test_energy_calculation(self, age, weight, height, sex, expected):
        """
        Profile's calculate energy method correctly calculates the EER.
        """
        profile = models.Profile(
            age=age,
            weight=weight,
            height=height,
            sex=sex,
            activity_level="LA",
        )

        assert profile.calculate_energy() == expected

    def test_profile_create_calculates_energy(self, db, user):
        """Saving a new profile record automatically calculates the EER."""
        profile = models.Profile(
            age=35, weight=80, height=180, sex="M", activity_level="LA", user=user
        )
        profile.save()
        profile.refresh_from_db()
        assert profile.energy_requirement is not None

    def test_profile_update_calculates_energy(self, db, saved_profile):
        """Updating a profile record automatically calculates the EER."""
        saved_profile.weight = 70
        saved_profile.save()

        saved_profile.refresh_from_db()
        assert saved_profile.energy_requirement == 2206

    def test_save_creating_entry_creates_a_weight_measurement_entry(
        self, profile, user
    ):
        profile.user = user
        profile.save()

        assert profile.weight_measurements.count() == 1

    def test_save_updating_add_measurement_true(self, saved_profile):
        saved_profile.weight = 70
        saved_profile.save(add_measurement=True)

        assert saved_profile.weight_measurements.count() == 2

    def test_save_updating_add_measurement_false(self, saved_profile):
        saved_profile.weight = 70
        saved_profile.save(add_measurement=False)

        assert saved_profile.weight_measurements.count() == 1

    def test_save_recalculate_weight_true_sets_weight_based_on_measurements(
        self, saved_profile
    ):
        saved_profile.weight_measurements.create(value=60)
        saved_profile.weight = 90

        saved_profile.save(recalculate_weight=True)

        assert saved_profile.weight == 70

    def test_save_recalculate_weight_true_add_measurement_true_includes_new_measurement(
        self, saved_profile
    ):
        saved_profile.weight = 90

        saved_profile.save(add_measurement=True, recalculate_weight=True)

        assert saved_profile.weight == 85

    def test_save_recalculate_weight_false_keeps_weight_set_on_instance(
        self, saved_profile
    ):
        saved_profile.weight_measurements.create(value=60)
        saved_profile.weight = 90

        saved_profile.save(recalculate_weight=False)

        assert saved_profile.weight == 90

    def test_current_weight_is_the_average_of_measurements_within_week_before_last(
        self, profile, user
    ):
        profile.user = user
        profile.save()
        last = profile.weight_measurements.first().date
        models.WeightMeasurement.objects.bulk_create(
            [
                models.WeightMeasurement(
                    profile=profile, date=last - timedelta(days=1), value=81
                ),
                models.WeightMeasurement(
                    profile=profile, date=last - timedelta(days=7), value=82
                ),
                models.WeightMeasurement(
                    profile=profile, date=last - timedelta(days=8), value=90
                ),  # This one is not included
            ]
        )
        # Average includes the measurement created when saving the
        # profile (value=80)
        assert profile.current_weight == 81

    def test_update_weight_sets_weight_to_current_weight(self, saved_profile):
        saved_profile.weight_measurements.create(value=90)
        saved_profile.update_weight()

        assert saved_profile.weight == 85

    @pytest.fixture
    def meal_2(self, saved_profile) -> models.Meal:
        """Another meal instance

        profile: saved_profile
        date: 2020-06-01
        """
        return models.Meal.objects.create(owner=saved_profile, date=date(2020, 6, 1))

    @pytest.fixture
    def meal_ingredient_2(self, meal, ingredient_2):
        """A MealIngredient instance.

        meal: meal
        ingredient: ingredient_2
        amount: 500
        """
        return models.MealIngredient.objects.create(
            meal=meal, ingredient=ingredient_2, amount=500
        )

    @pytest.fixture
    def meal_2_ingredient_1(self, meal_2, ingredient_1):
        """A MealIngredient instance.

        meal: meal_2
        ingredient: ingredient_1
        amount: 300
        """
        return models.MealIngredient.objects.create(
            meal=meal_2, ingredient=ingredient_1, amount=300
        )

    @pytest.fixture
    def meal_2_recipe(self, meal_2, recipe):
        """A MealRecipe instance.

        meal: meal_2
        recipe: recipe
        amount: 200
        """
        return models.MealRecipe.objects.create(meal=meal_2, recipe=recipe, amount=200)

    @pytest.fixture
    def multiple_weight_measurements(self, saved_profile):
        """WeightMeasurement instances.

        profile: saved_profile
        date: 2002-09-21
        value: 77.7

        profile: saved_profile
        date: 2022-09-21
        value: 80
        """
        ret = models.WeightMeasurement.objects.bulk_create(
            (
                models.WeightMeasurement(
                    profile=saved_profile,
                    date=datetime(year=2002, month=9, day=21),
                    value=77.7,
                ),
                models.WeightMeasurement(
                    profile=saved_profile,
                    date=datetime(year=2022, month=9, day=21),
                    value=80,
                ),
            )
        )
        return ret

    # Ingredient nutrient intake

    def test_intakes_from_ingredients_single_meal(
        self,
        saved_profile,
        meal,
        meal_ingredient,
        meal_ingredient_2,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_ingredients(nutrient_2.id)

        # 20 from meal_ingredient + 50 from meal_ingredient_2
        assert result == {date(2020, 6, 15): 70}

    def test_intakes_from_ingredients_multiple_meals(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_ingredients(nutrient_2.id)

        # 20 from meal_ingredient
        # + 50 from meal_ingredient_2
        # and 30 from meal_2_ingredient
        expected = {date(2020, 6, 15): 70, date(2020, 6, 1): 30}

        assert result == expected

    def test_intakes_from_ingredients_date_min(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_ingredients(
            nutrient_2.id, date_min=date(2020, 6, 2)
        )

        # 20 from meal_ingredient
        # + 50 from meal_ingredient_2
        expected = {date(2020, 6, 15): 70}

        assert result == expected

    def test_intakes_from_ingredients_date_max(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_ingredients(
            nutrient_2.id, date_max=date(2020, 6, 2)
        )

        # 20 from meal_ingredient
        # + 50 from meal_ingredient_2
        expected = {date(2020, 6, 1): 30}

        assert result == expected

    # Recipe nutrient intake

    def test_intakes_from_recipes_single_meal(
        self,
        saved_profile,
        meal,
        meal_recipe,
        recipe_ingredient,
        ingredient_nutrient_1_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_recipes(nutrient_2.id)

        # recipe final weight: 200, so:
        # 100 (meal_recipe)
        # * 100 (recipe_ingredient)
        # * 0.1 (ingredient_nutrient_2)
        # / 200 (meal.final_weight)
        expected = {date(2020, 6, 15): 5}

        assert result == expected

    def test_intakes_from_recipes_multiple_meals(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        ingredient_nutrient_1_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_recipes(nutrient_2.id)

        # recipe final weight: 200, so:
        # 100 (meal_recipe)
        # * 100 (recipe_ingredient)
        # * 0.1 (ingredient_nutrient_2)
        # / 200 (meal.final_weight)
        #
        # 200 (meal_recipe)
        # * 100 (recipe_ingredient)
        # * 0.1 (ingredient_nutrient_2)
        # / 200 (meal.final_weight)
        expected = {
            date(2020, 6, 15): 5,
            date(2020, 6, 1): 10,
        }

        assert result == expected

    def test_intakes_from_recipes_date_min(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        ingredient_nutrient_1_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_recipes(
            nutrient_2.id, date_min=date(2020, 6, 2)
        )

        expected = {date(2020, 6, 15): 5}

        assert result == expected

    def test_intakes_from_recipes_date_max(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        ingredient_nutrient_1_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_recipes(
            nutrient_2.id, date_max=date(2020, 6, 2)
        )

        expected = {date(2020, 6, 1): 10}

        assert result == expected

    def test_intakes_from_recipes_multiple_recipes(
        self,
        saved_profile,
        meal,
        meal_recipe,
        recipe_2,
        recipe_ingredient,
        ingredient_nutrient_1_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_from_recipes(nutrient_2.id)

        expected = {date(2020, 6, 15): 15}

        assert result == expected

    # Intakes by dates (combined)

    def test_intakes_by_date_only_ingredients(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_by_date(nutrient_2.id)

        expected = {date(2020, 6, 15): 70, date(2020, 6, 1): 30}

        assert result == expected

    def test_intakes_by_date_only_recipes(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        ingredient_nutrient_1_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_by_date(nutrient_2.id)

        expected = {
            date(2020, 6, 15): 5,
            date(2020, 6, 1): 10,
        }

        assert result == expected

    def test_intakes_by_date_both(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_by_date(nutrient_2.id)

        expected = {
            date(2020, 6, 15): 75,
            date(2020, 6, 1): 40,
        }

        assert result == expected

    def test_intakes_by_date_date_min(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_by_date(nutrient_2.id, date_min=date(2020, 6, 2))

        expected = {date(2020, 6, 15): 75}

        assert result == expected

    def test_intakes_by_date_date_max(
        self,
        saved_profile,
        meal,
        meal_2,
        meal_recipe,
        meal_2_recipe,
        recipe_ingredient,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        nutrient_2,
    ):
        result = saved_profile.intakes_by_date(nutrient_2.id, date_max=date(2020, 6, 2))

        expected = {date(2020, 6, 1): 40}

        assert result == expected

    def test_energy_progress_property_is_the_ratio_of_energy_intake_to_recommendation(
        self, profile
    ):
        expected = 9

        actual = profile.energy_progress(180)

        assert actual == expected

    def test_weight_by_date_returns_avg_value_by_date(
        self, saved_profile, multiple_weight_measurements
    ):
        date_ = date(year=2022, month=9, day=21)
        models.WeightMeasurement.objects.create(
            profile=saved_profile, date=date_, value=40
        )

        result = saved_profile.weight_by_date()

        assert result[date_] == 60

    def test_weight_by_date_date_min(self, saved_profile, multiple_weight_measurements):
        date_ = date(year=2022, month=9, day=21)

        result = saved_profile.weight_by_date(date_min=date_)

        assert date(year=2002, month=9, day=21) not in result
        assert date_ in result

    def test_weight_by_date_date_max(self, saved_profile, multiple_weight_measurements):
        date_ = date(year=2002, month=9, day=21)

        result = saved_profile.weight_by_date(date_max=date_)

        assert date(year=2022, month=9, day=21) not in result
        assert date_ in result


class TestWeightMeasurement:
    """Tests of the `WeightMeasurement` model."""

    def test_has_min_value_01_validation(self, saved_profile):
        instance = models.WeightMeasurement(profile=saved_profile, value=0)

        with pytest.raises(ValidationError):
            instance.full_clean()

        instance = models.WeightMeasurement(profile=saved_profile, value=0.1)
        try:
            instance.full_clean()
        except ValidationError:
            pytest.fail()

    def test_save_updates_profile_weight(self, saved_profile):
        models.WeightMeasurement.objects.create(profile=saved_profile, value=60)

        assert saved_profile.weight == 70

    def test_delete_updates_profile_weight(self, saved_profile, weight_measurement):
        weight_measurement.value = 100
        weight_measurement.date = date.today()
        weight_measurement.save()
        assert saved_profile.weight == 90

        weight_measurement.delete()

        assert saved_profile.weight == 80
