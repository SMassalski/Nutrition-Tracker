import pytest
from core import models


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
