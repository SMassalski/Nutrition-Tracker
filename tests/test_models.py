"""Tests of ORM models"""
from datetime import datetime

from main.models import (
    Ingredient,
    Meal,
    MealComponent,
    MealComponentIngredient,
    Nutrient,
)


# Ingredient model
def test_ingredient_string_representation():
    """Ingredient model's string representation is its name"""
    ingredient = Ingredient(dataset="test_dataset", name="test_name")
    assert str(ingredient) == ingredient.name


def test_ingredient_nutritional_value_returns_nutrient_amounts(
    db, ingredient_1, ingredient_nutrient_1_1, ingredient_nutrient_1_2
):
    """
    Ingredient.nutritional_value() returns a mapping of nutrients in the ingredient
    to their amounts in the ingredient.
    """
    result = ingredient_1.nutritional_value()
    assert result[ingredient_nutrient_1_1.nutrient] == ingredient_nutrient_1_1.amount
    assert result[ingredient_nutrient_1_2.nutrient] == ingredient_nutrient_1_2.amount


# Nutrient model
def test_nutrient_string_representation():
    """
    Nutrient model's string representation follows the format
    <name> (<pretty unit symbol>).
    """
    nutrient = Nutrient(name="test_name", unit="UG")
    assert str(nutrient) == f"{nutrient.name} ({Nutrient.PRETTY_UNITS[nutrient.unit]})"


# Meal Component model
def test_meal_component_string_representation():
    """MealComponent model's string representation is its name"""
    assert str(MealComponent(name="test_meal_component")) == "test_meal_component"


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


# Meal Component Ingredient model
def test_meal_component_ingredient_string_representation():
    """
    MealComponentIngredient model's string representation is the name of
    the component and the ingredient.
    """
    ingredient = Ingredient(name="test_ingredient")
    component = MealComponent(name="test_component")
    meal_component_ingredient = MealComponentIngredient(
        ingredient=ingredient, meal_component=component
    )
    assert str(meal_component_ingredient) == "test_component - test_ingredient"


# Meal model
def test_meal_string_representation():
    """
    Meal model's string representation is its name and formatted date.
    """
    meal = Meal(
        name="test_meal", date=datetime(day=1, month=1, year=2000, hour=12, minute=0)
    )
    assert str(meal) == "test_meal (12:00 - 01 Jan 2000)"


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
    meal_component_2 = MealComponent.objects.create(
        name="test_component_2", final_weight=100
    )
    ingredient_3 = Ingredient(name="test_ingredient_3", fdc_id=111, dataset="dataset")
    ingredient_3.save()
    ingredient_3.nutrients.create(nutrient=nutrient_1, amount=20)
    meal_component_2.ingredients.create(ingredient=ingredient_3, amount=100)
    meal = Meal.objects.create(user=user, name="test_meal")

    # 100g each of meal_component and meal_component_2
    meal.components.create(component=meal_component, amount=100)
    meal.components.create(component=meal_component_2, amount=100)

    result = meal.nutritional_value()
    assert result[nutrient_1] == 20.75
    assert result[nutrient_2] == 10
