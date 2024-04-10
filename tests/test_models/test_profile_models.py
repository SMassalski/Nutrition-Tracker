"""Tests of profile related features."""
from datetime import date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from main import models


@pytest.fixture
def meal_2(saved_profile) -> models.Meal:
    """Another meal instance

    profile: saved_profile
    date: 2020-06-01
    """
    return models.Meal.objects.create(owner=saved_profile, date=date(2020, 6, 1))


@pytest.fixture
def meal_2_ingredient_1(meal_2, ingredient_1):
    """A MealIngredient instance.

    meal: meal_2
    ingredient: ingredient_1
    amount: 300
    """
    return models.MealIngredient.objects.create(
        meal=meal_2, ingredient=ingredient_1, amount=300
    )


@pytest.fixture
def meal_ingredients(meal_ingredient, meal_ingredient_2, meal_2_ingredient_1):
    """Load meal ingredient fixtures.

    meal_ingredient
    meal_ingredient_2
    meal_2_ingredient_1
    """


@pytest.fixture
def recipes(meal_recipe, meal_2_recipe, recipe_ingredient):
    """Load recipe fixtures

    meal_recipe
    meal_2_recipe
    recipe_ingredient
    """


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

    def test_energy_progress_property_is_the_ratio_of_energy_intake_to_recommendation(
        self, profile
    ):
        expected = 9

        actual = profile.energy_progress(180)

        assert actual == expected

    def test_current_weight_no_measurements_returns_none(self, saved_profile):
        saved_profile.weight_measurements.all().delete()

        assert saved_profile.current_weight is None

    def test_save_recalculate_weight_ignored_if_profile_has_no_measurements(
        self, saved_profile
    ):
        saved_profile.weight_measurements.all().delete()

        saved_profile.save(recalculate_weight=True)

        assert saved_profile.weight == 80


class TestProfileWeightByDate:
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


class TestProfileIntakeByDate:
    # Ingredient nutrient intake

    @pytest.fixture(autouse=True)
    def base_fixtures(self, ingredient_nutrient_1_2, ingredient_nutrient_2_2):
        """Load base fixtures.

        ingredient_nutrient_1_2
        ingredient_nutrient_2_2
        """
        pass

    def test_intakes_from_ingredients_single_meal(
        self, saved_profile, meal, meal_ingredient, meal_ingredient_2, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_ingredients(nutrient_2.id)

        # 20 from meal_ingredient + 50 from meal_ingredient_2
        assert result == {date(2020, 6, 15): 70}

    def test_intakes_from_ingredients_multiple_meals(
        self, saved_profile, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_ingredients(nutrient_2.id)

        # 20 from meal_ingredient
        # + 50 from meal_ingredient_2
        # and 30 from meal_2_ingredient
        expected = {date(2020, 6, 15): 70, date(2020, 6, 1): 30}

        assert result == expected

    def test_intakes_from_ingredients_date_min(
        self, saved_profile, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_ingredients(
            nutrient_2.id, date_min=date(2020, 6, 2)
        )

        # 20 from meal_ingredient
        # + 50 from meal_ingredient_2
        expected = {date(2020, 6, 15): 70}

        assert result == expected

    def test_intakes_from_ingredients_date_max(
        self, saved_profile, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_ingredients(
            nutrient_2.id, date_max=date(2020, 6, 2)
        )

        # 20 from meal_ingredient
        # + 50 from meal_ingredient_2
        expected = {date(2020, 6, 1): 30}

        assert result == expected

    # Recipe nutrient intake

    def test_intakes_from_recipes_single_meal(
        self, saved_profile, meal, meal_recipe, recipe_ingredient, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_recipes(nutrient_2.id)

        # recipe final weight: 200, so:
        # 100 (meal_recipe)
        # * 100 (recipe_ingredient)
        # * 0.1 (ingredient_nutrient_2)
        # / 200 (meal.final_weight)
        expected = {date(2020, 6, 15): 5}

        assert result == expected

    def test_intakes_from_recipes_multiple_meals(
        self, saved_profile, recipes, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_recipes(nutrient_2.id)

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

    def test_intakes_from_recipes_date_min(self, saved_profile, recipes, nutrient_2):
        result = saved_profile.nutrient_intakes_from_recipes(
            nutrient_2.id, date_min=date(2020, 6, 2)
        )

        expected = {date(2020, 6, 15): 5}

        assert result == expected

    def test_intakes_from_recipes_date_max(self, saved_profile, recipes, nutrient_2):
        result = saved_profile.nutrient_intakes_from_recipes(
            nutrient_2.id, date_max=date(2020, 6, 2)
        )

        expected = {date(2020, 6, 1): 10}

        assert result == expected

    def test_intakes_from_recipes_multiple_recipes(
        self, saved_profile, meal, meal_recipe, recipe_2, recipe_ingredient, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_from_recipes(nutrient_2.id)

        expected = {date(2020, 6, 15): 15}

        assert result == expected

    # Intakes by dates (combined)

    def test_intakes_by_date_only_ingredients(
        self, saved_profile, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_by_date(nutrient_2.id)

        expected = {date(2020, 6, 15): 70, date(2020, 6, 1): 30}

        assert result == expected

    def test_intakes_by_date_only_recipes(self, saved_profile, recipes, nutrient_2):
        result = saved_profile.nutrient_intakes_by_date(nutrient_2.id)

        expected = {
            date(2020, 6, 15): 5,
            date(2020, 6, 1): 10,
        }

        assert result == expected

    def test_intakes_by_date_both(
        self, saved_profile, recipes, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_by_date(nutrient_2.id)

        expected = {
            date(2020, 6, 15): 75,
            date(2020, 6, 1): 40,
        }

        assert result == expected

    def test_intakes_by_date_date_min(
        self, saved_profile, recipes, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_by_date(
            nutrient_2.id, date_min=date(2020, 6, 2)
        )

        expected = {date(2020, 6, 15): 75}

        assert result == expected

    def test_intakes_by_date_date_max(
        self, saved_profile, recipes, meal_ingredients, nutrient_2
    ):
        result = saved_profile.nutrient_intakes_by_date(
            nutrient_2.id, date_max=date(2020, 6, 2)
        )

        expected = {date(2020, 6, 1): 40}

        assert result == expected


class TestCaloriesByDate:
    @pytest.fixture(autouse=True)
    def ingredients_and_nutrients(
        self,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        nutrient_2_energy,
    ):
        """Load base fixtures

        ingredient_nutrient_1_1
        ingredient_nutrient_1_2
        nutrient_1_energy
        nutrient_2_energy
        """
        pass

    @pytest.fixture
    def meal_ingredients(
        self,
        meal_ingredient,
        meal_ingredient_2,
        meal_2_ingredient_1,
        ingredient_nutrient_2_2,
    ):
        """Load meal ingredient fixtures.

        meal_ingredient
        meal_ingredient_2
        meal_2_ingredient_1
        ingredient_nutrient_2_2
        """

    # Ingredient calories

    def test_calories_from_ingredients_single_meal(
        self, saved_profile, meal_ingredient, meal_ingredient_2, ingredient_nutrient_2_2
    ):
        expected = {
            date(year=2020, month=6, day=15): {
                "test_nutrient": 3000,
                "test_nutrient_2": 280,
            }
        }
        actual = saved_profile.calories_from_ingredients()

        assert actual == expected

    def test_calories_from_ingredients_multiple_meals(
        self, saved_profile, meal_ingredients
    ):
        expected = {
            date(2020, 6, 15): {
                "test_nutrient": 3000,
                "test_nutrient_2": 280,
            },
            date(2020, 6, 1): {
                "test_nutrient": 4500,
                "test_nutrient_2": 120,
            },
        }

        actual = saved_profile.calories_from_ingredients()

        assert actual == expected

    def test_calories_from_ingredients_date_min(self, saved_profile, meal_ingredients):
        expected = {
            date(2020, 6, 15): {
                "test_nutrient": 3000,
                "test_nutrient_2": 280,
            }
        }

        actual = saved_profile.calories_from_ingredients(date_min=date(2020, 6, 2))

        assert actual == expected

    def test_calories_from_ingredients_date_max(self, saved_profile, meal_ingredients):
        expected = {
            date(2020, 6, 1): {
                "test_nutrient": 4500,
                "test_nutrient_2": 120,
            }
        }

        actual = saved_profile.calories_from_ingredients(date_max=date(2020, 6, 2))

        assert actual == expected

    # Recipe calories

    def test_calories_from_recipes_single_meal(
        self, saved_profile, meal_recipe, recipe_ingredient
    ):

        expected = {
            date(2020, 6, 15): {"test_nutrient": 750.0, "test_nutrient_2": 20.0}
        }

        actual = saved_profile.calories_from_recipes()

        assert actual == expected

    def test_calories_from_recipes_multiple_meals(self, saved_profile, recipes):
        expected = {
            date(2020, 6, 15): {"test_nutrient": 750.0, "test_nutrient_2": 20.0},
            date(2020, 6, 1): {"test_nutrient": 1500.0, "test_nutrient_2": 40.0},
        }

        actual = saved_profile.calories_from_recipes()

        assert actual == expected

    def test_calories_from_recipes_date_min(self, saved_profile, recipes):

        expected = {
            date(2020, 6, 15): {"test_nutrient": 750.0, "test_nutrient_2": 20.0}
        }

        actual = saved_profile.calories_from_recipes(date_min=date(2020, 6, 2))

        assert actual == expected

    def test_calories_from_recipes_date_max(self, saved_profile, recipes):
        expected = {
            date(2020, 6, 1): {"test_nutrient": 1500.0, "test_nutrient_2": 40.0}
        }

        actual = saved_profile.calories_from_recipes(date_max=date(2020, 6, 2))

        assert actual == expected

    def test_calories_from_recipes_multiple_recipes(
        self, saved_profile, meal_recipe, recipe_2, recipe_ingredient
    ):

        expected = {
            date(2020, 6, 15): {"test_nutrient": 2250.0, "test_nutrient_2": 60.0}
        }

        actual = saved_profile.calories_from_recipes()

        assert actual == expected

    # Calories by dates (combined)

    def test_calories_by_date_only_ingredients(self, saved_profile, meal_ingredients):
        expected = {
            date(2020, 6, 15): {"test_nutrient": 3000.0, "test_nutrient_2": 280.0},
            date(2020, 6, 1): {"test_nutrient": 4500.0, "test_nutrient_2": 120.0},
        }

        actual = saved_profile.calories_by_date()

        assert actual == expected

    def test_calories_by_date_only_recipes(self, saved_profile, meal, recipes):
        expected = {
            date(2020, 6, 15): {"test_nutrient": 750.0, "test_nutrient_2": 20.0},
            date(2020, 6, 1): {"test_nutrient": 1500.0, "test_nutrient_2": 40.0},
        }

        actual = saved_profile.calories_by_date()

        assert actual == expected

    def test_calories_by_date_both(self, saved_profile, recipes, meal_ingredients):

        expected = {
            date(2020, 6, 15): {"test_nutrient": 3750.0, "test_nutrient_2": 300.0},
            date(2020, 6, 1): {"test_nutrient": 6000.0, "test_nutrient_2": 160.0},
        }

        actual = saved_profile.calories_by_date()

        assert actual == expected

    def test_calories_by_date_date_min(self, saved_profile, recipes, meal_ingredients):
        expected = {
            date(2020, 6, 15): {"test_nutrient": 3750.0, "test_nutrient_2": 300.0},
        }

        actual = saved_profile.calories_by_date(date_min=date(2020, 6, 2))

        assert actual == expected

    def test_calories_by_date_date_max(self, saved_profile, recipes, meal_ingredients):
        expected = {
            date(2020, 6, 1): {"test_nutrient": 6000.0, "test_nutrient_2": 160.0},
        }

        actual = saved_profile.calories_by_date(date_max=date(2020, 6, 2))

        assert actual == expected


class TestProfileAverageIntakes:
    @pytest.fixture(autouse=True)
    def base_fixture(
        self, ingredient_nutrient_1_1, ingredient_nutrient_1_2, ingredient_nutrient_2_2
    ):
        """Load base fixtures.

        ingredient_nutrient_1_1
        ingredient_nutrient_1_2
        ingredient_nutrient_2_2
        """

    # from ingredients

    def test_ingredient_intakes_multiple_meals(
        self, saved_profile, meal_ingredients, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 1): 450, date(2020, 6, 15): 300},
            nutrient_2.id: {date(2020, 6, 1): 30, date(2020, 6, 15): 70},
        }

        actual = saved_profile.ingredient_intakes()

        assert actual == expected

    def test_ingredient_intakes_date_min(
        self, saved_profile, meal_ingredients, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 15): 300},
            nutrient_2.id: {date(2020, 6, 15): 70},
        }

        actual = saved_profile.ingredient_intakes(date_min=date(2020, 6, 15))

        assert actual == expected

    def test_ingredient_intakes_date_max(
        self, saved_profile, meal_ingredients, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 1): 450},
            nutrient_2.id: {date(2020, 6, 1): 30},
        }

        actual = saved_profile.ingredient_intakes(date_max=date(2020, 6, 1))

        assert actual == expected

    # from recipes

    def test_recipe_intakes_multiple_meals(
        self, saved_profile, recipes, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 1): 150, date(2020, 6, 15): 75},
            nutrient_2.id: {date(2020, 6, 1): 10, date(2020, 6, 15): 5},
        }

        actual = saved_profile.recipe_intakes()

        assert actual == expected

    def test_recipe_intakes_multiple_recipes(
        self, saved_profile, recipes, recipe_2, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 1): 150, date(2020, 6, 15): 225},
            nutrient_2.id: {date(2020, 6, 1): 10, date(2020, 6, 15): 15},
        }

        actual = saved_profile.recipe_intakes()

        assert actual == expected

    def test_recipe_intakes_date_min(
        self, saved_profile, recipes, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 15): 75},
            nutrient_2.id: {date(2020, 6, 15): 5},
        }

        actual = saved_profile.recipe_intakes(date_min=date(2020, 6, 15))

        assert actual == expected

    def test_recipe_intakes_date_max(
        self, saved_profile, recipes, nutrient_1, nutrient_2
    ):

        expected = {
            nutrient_1.id: {date(2020, 6, 1): 150},
            nutrient_2.id: {date(2020, 6, 1): 10},
        }

        actual = saved_profile.recipe_intakes(date_max=date(2020, 6, 1))

        assert actual == expected

    # average

    def test_average_intakes_ingredients_only(
        self, saved_profile, meal_ingredients, nutrient_1, nutrient_2
    ):
        expected = {
            nutrient_1.id: 375,
            nutrient_2.id: 50,
        }

        actual = saved_profile.average_intakes()

        assert actual == expected

    def test_average_intakes_recipes_only(
        self, saved_profile, recipes, nutrient_1, nutrient_2
    ):
        expected = {
            nutrient_1.id: 112.5,
            nutrient_2.id: 7.5,
        }

        actual = saved_profile.average_intakes()

        assert actual == expected

    def test_average_intakes_recipes_only_multiple_recipes(
        self, saved_profile, recipes, recipe_2, nutrient_1, nutrient_2
    ):
        expected = {
            nutrient_1.id: 187.5,
            nutrient_2.id: 12.5,
        }

        actual = saved_profile.average_intakes()

        assert actual == expected

    def test_average_intakes_ingredients_and_recipes(
        self, saved_profile, meal_ingredients, recipes, nutrient_1, nutrient_2
    ):
        expected = {
            nutrient_1.id: 487.5,
            nutrient_2.id: 57.5,
        }

        actual = saved_profile.average_intakes()

        assert actual == expected

    def test_average_intakes_date_min(
        self, saved_profile, meal_ingredients, recipes, nutrient_1, nutrient_2
    ):
        expected = {
            nutrient_1.id: 375,
            nutrient_2.id: 75,
        }

        actual = saved_profile.average_intakes(date_min=date(2020, 6, 15))

        assert actual == expected

    def test_average_intakes_date_max(
        self, saved_profile, meal_ingredients, recipes, nutrient_1, nutrient_2
    ):
        expected = {
            nutrient_1.id: 600,
            nutrient_2.id: 40,
        }

        actual = saved_profile.average_intakes(date_max=date(2020, 6, 1))

        assert actual == expected


class TestProfileMalnutrition:
    @pytest.fixture(autouse=True)
    def base_fixtures(self, ingredient_nutrient_1_1, ingredient_nutrient_1_2):
        """Load base fixtures.

        ingredient_nutrient_1_1
        ingredient_nutrient_1_2
        """

    def test_malnutrition_only_uses_recommendations_for_profile(
        self,
        saved_profile,
        meal_ingredients,
        nutrient_1,
        nutrient_2,
    ):
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            sex="B",
            amount_min=1000,
        )
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_2,
            sex="M",
            amount_min=1000,
        )

        results = saved_profile.malnutrition()

        assert nutrient_1.id in results
        assert nutrient_2.id not in results

    def test_malnutrition_threshold_none_includes_all_malconsumed_nutrients(
        self,
        saved_profile,
        meal_ingredients,
        nutrient_1,
        nutrient_2,
    ):
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            sex="B",
            amount_min=1000,
        )
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_2,
            sex="B",
            amount_min=1000,
        )

        results = saved_profile.malnutrition()

        assert nutrient_1.id in results
        assert nutrient_2.id in results

    def test_malnutrition_threshold_limits_malconsumed_nutrients_based_on_magnitude(
        self,
        saved_profile,
        meal_ingredients,
        nutrient_1,
        nutrient_2,
    ):
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            sex="B",
            amount_min=500,
        )
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_2,
            sex="B",
            amount_min=500,
        )

        results = saved_profile.malnutrition(threshold=0.95)

        assert nutrient_1.id not in results
        assert nutrient_2.id in results

    def test_malnutrition_magnitude_under_matches_formula(
        self,
        saved_profile,
        meal_ingredients,
        nutrient_1,
    ):
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            sex="B",
            amount_min=500,
        )
        # (amount_min - intake) / amount_min
        expected = (500 - 375) / 500

        actual = saved_profile.malnutrition()[nutrient_1.id]

        assert actual == expected

    def test_malnutrition_magnitude_over_matches_formula(
        self,
        saved_profile,
        meal_ingredients,
        nutrient_1,
    ):
        models.IntakeRecommendation.objects.create(
            age_min=0,
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            sex="B",
            amount_max=250,
        )
        # (intake - amount_max) / amount_max
        expected = (375 - 250) / 250

        actual = saved_profile.malnutrition()[nutrient_1.id]

        assert actual == expected


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
