"""Tests of models related to meal / recipe features."""
from datetime import datetime

import pytest
from main import models


@pytest.fixture
def meal_component(db, ingredient_1, ingredient_2):
    """Meal component record and instance.

    The component consists of ingredient_1 and ingredient_2.

    name: test_component
    final_weight: 200

    ingredients:

        - ingredient: ingredient_1
        - amount: 100

        - ingredient: ingredient_2
        - amount: 200
    """
    instance = models.MealComponent(name="test_component", final_weight=200)
    instance.save()
    instance.ingredients.create(ingredient=ingredient_1, amount=100)
    instance.ingredients.create(ingredient=ingredient_2, amount=100)
    return instance


# Meal Component model


def test_meal_component_nutritional_value_calculates_nutrients(
    db, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, meal_component
):
    """
    MealComponent.nutritional_value() calculates the amount of
    each nutrient in 100g of a component.
    """
    # INFO
    # 10g of nutrient_2 in 100g of ingredient_1
    # 10g of nutrient_2 in 100g of ingredient_2

    assert meal_component.nutritional_value()[nutrient_2] == 10


def test_meal_component_nutritional_value_is_correct_with_different_final_weight(
    db, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, meal_component
):
    """
    MealComponent.nutritional_value() calculates the amount of
    each nutrient in 100g of a component when the final weight of the
    component is not equal to the sum of the ingredient weight.
    """
    # INFO
    # 10g of nutrient_2 in 100g of ingredient_1
    # 10g of nutrient_2 in 100g of ingredient_2

    meal_component.final_weight = 50
    assert meal_component.nutritional_value()[nutrient_2] == 40


# Meal model
class TestMeal:
    """Tests of the meal model."""

    def test_get_intake_no_ingredients(self, meal):
        """
        Meal.get_intakes() returns an empty dict if the meal doesn't
        have any ingredients.
        """
        result = meal.get_intakes()

        assert result == {}

    def test_get_intake_single_ingredient(
        self, ingredient_nutrient_1_1, ingredient_1, nutrient_1, meal
    ):
        """
        Meal.get_intakes() returns the nutrient intakes of a meal with
        a single ingredient and amount of 1.
        """
        meal.mealingredient_set.create(ingredient=ingredient_1, amount=1)
        expected_amount = 0.015  # ingredient_nutrient amounts are per 100g

        result = meal.get_intakes()

        assert result[nutrient_1.id] == expected_amount

    def test_get_intake_single_ingredient_amount_changed(
        self, ingredient_nutrient_1_1, ingredient_1, nutrient_1, meal
    ):
        """
        Meal.get_intakes() returns the nutrient intakes of a meal with
        a single ingredient and an amount other than 1.
        """
        meal.mealingredient_set.create(ingredient=ingredient_1, amount=5)
        expected_amount = 0.075  # ingredient_nutrient amounts are per 100g

        result = meal.get_intakes()

        assert result[nutrient_1.id] == expected_amount

    def test_get_intake_single_ingredient_multiple_nutrients(
        self,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_1,
        nutrient_1,
        nutrient_2,
        meal,
    ):
        """
        Meal.get_intakes() returns the nutrient intakes of a meal with
        a single ingredient that has multiple nutrients.
        """
        meal.mealingredient_set.create(ingredient=ingredient_1, amount=2)
        expected = {
            nutrient_1.id: 0.03,
            nutrient_2.id: 0.2,
        }  # ingredient_nutrient amounts are per 100g

        result = meal.get_intakes()

        assert result == expected

    def test_get_intake_multiple_ingredients(
        self,
        meal,
        ingredient_1,
        ingredient_2,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
    ):
        """
        Meal.get_intakes() returns the nutrient intakes of a meal with
        multiple ingredients.
        """
        meal.mealingredient_set.create(ingredient=ingredient_1, amount=2)
        meal.mealingredient_set.create(ingredient=ingredient_2, amount=3)
        expected = {
            nutrient_1.id: 0.03,
            nutrient_2.id: 0.5,
        }  # ingredient_nutrient amounts are per 100g

        result = meal.get_intakes()

        assert result == expected
