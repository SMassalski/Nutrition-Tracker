"""Tests of ORM models"""
from main.models import Ingredient, Nutrient


def test_ingredient_string_representation():
    """Ingredient model's string representation is its name"""
    ingredient = Ingredient(dataset="test_dataset", name="test_name")
    assert str(ingredient) == ingredient.name


def test_nutrient_string_representation():
    """
    Nutrient model's string representation follows the format
    <name> (<pretty unit symbol>).
    """
    nutrient = Nutrient(name="test_name", unit="UG")
    assert str(nutrient) == f"{nutrient.name} ({Nutrient.PRETTY_UNITS[nutrient.unit]})"
