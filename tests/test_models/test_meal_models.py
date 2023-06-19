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


def test_meal_nutritional_value_calculates_nutrients(
    db,
    ingredient_nutrient_1_1,
    ingredient_nutrient_1_2,
    ingredient_nutrient_2_2,
    nutrient_1,
    nutrient_2,
    meal_component,
    user,
):
    """
    Meal.nutritional_value() calculates the amount of each nutrient in
    the meal.
    """
    # INFO
    # 0.75g of nutrient_1 in 100g of meal_component
    # 10g of nutrient_2 in 100g of meal_component

    # 20g of nutrient_1 in 100g of meal_component_2
    meal_component_2 = models.MealComponent.objects.create(
        name="test_component_2", final_weight=100
    )
    ingredient_3 = models.Ingredient(
        name="test_ingredient_3", external_id=111, dataset="dataset"
    )
    ingredient_3.save()
    ingredient_3.ingredientnutrient_set.create(nutrient=nutrient_1, amount=20)
    meal_component_2.ingredients.create(ingredient=ingredient_3, amount=100)
    meal = models.Meal.objects.create(user=user, name="test_meal")

    # 100g each of meal_component and meal_component_2
    meal.components.create(component=meal_component, amount=100)
    meal.components.create(component=meal_component_2, amount=100)

    result = meal.nutritional_value()
    assert result[nutrient_1] == 20.75
    assert result[nutrient_2] == 10
