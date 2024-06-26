"""Model test fixtures."""
import pytest
from core import models


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


@pytest.fixture
def recipe_2(meal, ingredient_1):
    """Recipe instance.

    name: "S"
    owner: saved_profile

    MealRecipe:
    meal: meal
    amount: 100

    ingredient: ingredient_1
    amount: 50
    """
    recipe_2 = models.Recipe.objects.create(owner=meal.owner, name="S")
    recipe_2.recipeingredient_set.create(ingredient=ingredient_1, amount=50)
    meal.mealrecipe_set.create(recipe=recipe_2, amount=100)
    return recipe_2


@pytest.fixture
def meal_ingredient_2(meal, ingredient_2):
    """A MealIngredient instance.

    meal: meal
    ingredient: ingredient_2
    amount: 500
    """
    return models.MealIngredient.objects.create(
        meal=meal, ingredient=ingredient_2, amount=500
    )


@pytest.fixture
def meal_2_recipe(meal_2, recipe):
    """A MealRecipe instance.

    meal: meal_2
    recipe: recipe
    amount: 200
    """
    return models.MealRecipe.objects.create(meal=meal_2, recipe=recipe, amount=200)
