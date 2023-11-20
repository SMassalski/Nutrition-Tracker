"""Model test fixtures."""
import pytest
from main import models


@pytest.fixture
def ingredient_nutrient_1_2(db, ingredient_1, nutrient_2):
    """
    IngredientNutrient associating nutrient_2 with ingredient_1.

    amount: 0.1
    """
    amount = 0.1
    return models.IngredientNutrient.objects.create(
        nutrient=nutrient_2, ingredient=ingredient_1, amount=amount
    )


@pytest.fixture
def ingredient_nutrient_2_2(db, ingredient_2, nutrient_2):
    """
    IngredientNutrient associating nutrient_2 with ingredient_2.

    amount: 0.1
    """
    amount = 0.1
    return models.IngredientNutrient.objects.create(
        nutrient=nutrient_2, ingredient=ingredient_2, amount=amount
    )
