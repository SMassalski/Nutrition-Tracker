"""Utility function test fixtures"""
import pytest

from ..dummies import DummyIngredient, DummyIngredientNutrient, DummyNutrient


@pytest.fixture
def dummy_nutrient_class():
    """Clear DummyNutrient saved list after test."""
    yield DummyNutrient
    DummyNutrient.clear_saved()


@pytest.fixture
def dummy_ingredient_class():
    """Clear DummyIngredient saved list after test."""
    yield DummyIngredient
    DummyIngredient.clear_saved()


@pytest.fixture
def dummy_ingredient_nutrient_class():
    """Clear DummyIngredientNutrient saved list after test."""
    yield DummyIngredientNutrient
    DummyIngredientNutrient.clear_saved()
