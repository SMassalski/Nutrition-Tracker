"""Model test fixtures."""
import pytest
from main import models


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


@pytest.fixture
def component(nutrient_1, nutrient_2):
    """Component relationship between nutrient_1 and nutrient_2

    target: nutrient_2
    component: nutrient_1
    """
    return models.NutrientComponent.objects.create(
        target=nutrient_2, component=nutrient_1
    )
