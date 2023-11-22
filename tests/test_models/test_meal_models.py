"""Tests of models related to meal / recipe features."""
import pytest
from main import models


@pytest.fixture
def recipe(recipe, ingredient_1, ingredient_2):
    """Recipe record and instance.

    name: test_recipe
    final_weight: 200

    ingredients:

        - ingredient: ingredient_1
        - amount: 100

        - ingredient: ingredient_2
        - amount: 100
    """
    recipe.recipeingredient_set.create(ingredient=ingredient_1, amount=100)
    recipe.recipeingredient_set.create(ingredient=ingredient_2, amount=100)
    return recipe


@pytest.fixture
def ingredient_nutrient_1_1(ingredient_nutrient_1_1) -> models.IngredientNutrient:
    """
    IngredientNutrient associating nutrient_1 with ingredient_1.

    amount: 0.015
    """
    ingredient_nutrient_1_1.amount = 0.015
    ingredient_nutrient_1_1.save()
    return ingredient_nutrient_1_1


class TestRecipe:
    def test_nutritional_value_calculates_nutrients_per_gram(
        self, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, recipe
    ):
        # 100 * nutrient_1 + 100 * nutrient_2 / 200 (final_weight)
        assert recipe.nutritional_value()[nutrient_2.id] == 0.1

    def test_nutritional_value_uses_ingredient_amount_sum_if_final_weight_is_null(
        self, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, recipe
    ):
        recipe.final_weight = None
        recipe.save()

        # 100 * nutrient_1 + 100 * nutrient_2 / 200
        assert recipe.nutritional_value()[nutrient_2.id] == 0.1

    def test_get_intakes_calculates_nutrients_per_100_gram(
        self, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, recipe
    ):
        # 100 * nutrient_1 + 100 * nutrient_2 / 200 (final_weight) * 100g
        assert recipe.get_intakes()[nutrient_2.id] == 10

    def test_calories_calculates_energy_from_nutrients_in_recipe_per_gram(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_1_energy,
        recipe,
    ):
        # ingredient_nutrient_1_1 amount * nutrient_1_energy amount
        # * amount of ingredient in the recipe / recipe final weight
        expected = 0.015 * 10 * 0.5
        assert recipe.calories == {nutrient_1.name: expected}

    def test_ingredient_calories_results_ordered_alphabetically(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        recipe,
    ):
        models.NutrientEnergy.objects.create(nutrient=nutrient_2, amount=2)

        assert list(recipe.calories.keys()) == [nutrient_1.name, nutrient_2.name]

    def test_calories_only_returns_nutrients_with_energy(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        recipe,
    ):
        result = recipe.calories

        assert nutrient_1.name in result
        assert nutrient_2.name not in result

    def test_calories_excludes_component_nutrients(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        nutrient_1_energy,
        component,
        recipe,
    ):

        result = recipe.calories

        assert nutrient_1.name not in result

    def test_calories_excludes_child_type_nutrients(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        nutrient_1_energy,
        recipe,
    ):
        type_ = models.NutrientType.objects.create(parent_nutrient=nutrient_2)
        nutrient_1.types.add(type_)

        result = recipe.calories

        assert nutrient_1.name not in result

    def test_calories_uses_sum_of_ingredient_amounts_if_final_weight_is_null(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_1_energy,
        recipe,
    ):
        recipe.final_weight = None
        recipe.save()

        # ingredient_nutrient_1_1 amount * nutrient_1_energy amount
        # * amount of ingredient in the recipe / recipe weight
        expected = 0.015 * 10 * 0.5
        assert recipe.calories == {nutrient_1.name: expected}

    def test_get_slug_unique_name(self, recipe):
        recipe.name = "Test Recipe"
        expected = "test-recipe-1"

        assert recipe.get_slug() == expected

    def test_get_slug_duplicate_name_increments_slug_number(self, recipe):
        expected = "test-recipe-2"
        recipe.name = "Test Recipe"
        recipe.save()

        recipe = models.Recipe(name="Test Recipe", owner=recipe.owner)

        assert recipe.get_slug() == expected

    def test_get_slug_not_exact_duplicate_name_increments_slug_number(self, recipe):
        expected = "test-recipe-2"
        recipe.name = "Test  recipe "
        recipe.save()

        recipe = models.Recipe(name="Test Recipe", owner=recipe.owner)

        assert recipe.get_slug() == expected

    def test_get_slug_slug_already_correct_stays_the_same(self, recipe):
        expected = "test-recipe-1"
        recipe.name = "Test recipe"
        recipe.save()

        recipe.name = "test recipe"

        assert recipe.get_slug() == expected

    def test_save_generates_slug(self, saved_profile):
        expected = "test-recipe-1"
        recipe = models.Recipe(owner=saved_profile, name="test recipe", final_weight=1)

        recipe.save()

        assert recipe.slug == expected


# Meal model
class TestMeal:
    """Tests of the meal model."""

    @pytest.fixture
    def meal_ingredients(self, meal, ingredient_1, ingredient_2):
        """Meal ingredient entries.

        ingredient: ingredient_1
        amount: 2
        meal: meal

        ingredient: ingredient_2
        amount: 3
        meal: meal
        """
        a = meal.mealingredient_set.create(ingredient=ingredient_1, amount=2)
        b = meal.mealingredient_set.create(ingredient=ingredient_2, amount=3)

        return a, b

    @pytest.fixture
    def meal_recipe(self, meal, recipe):
        """A RecipeAmount entry.

        meal: meal
        recipe: recipe
        amount: 100
        """
        meal.mealrecipe_set.create(amount=100, recipe=recipe)

    def test_ingredient_intake_no_ingredients(self, meal):
        """
        Meal.ingredient_intakes() returns an empty dict if the meal doesn't
        have any ingredients.
        """
        result = meal.ingredient_intakes()

        assert result == {}

    def test_ingredient_intake(
        self,
        meal,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        meal_ingredients,
    ):

        expected = {
            nutrient_1.id: 0.03,
            nutrient_2.id: 0.5,
        }

        result = meal.ingredient_intakes()

        assert result == expected

    def test_ingredient_intake_num_queries(
        self,
        meal,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        meal_ingredients,
        django_assert_num_queries,
    ):
        with django_assert_num_queries(1):
            meal.ingredient_intakes()

    def test_recipe_intake_no_recipes(self, meal):
        result = meal.ingredient_intakes()

        assert result == {}

    def test_recipe_intake(
        self,
        meal,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        meal_recipe,
    ):
        # nutrient_1: 0.015; nutrient_2: 0.2
        # ingredient_1: 100; ingredient_2: 100; final_weight: 200;

        expected = {
            nutrient_1.id: 0.75,
            nutrient_2.id: 10,
        }

        result = meal.recipe_intakes()

        assert result == expected

    def test_recipe_intakes_uses_ingredient_amount_sums_if_final_weight_is_null(
        self,
        meal,
        recipe,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        meal_recipe,
    ):
        recipe.final_weight = None
        recipe.save()

        expected = {
            nutrient_1.id: 0.75,
            nutrient_2.id: 10,
        }

        result = meal.recipe_intakes()

        assert result == expected

    def test_recipe_intake_num_queries(
        self,
        meal,
        meal_recipe,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        django_assert_num_queries,
    ):
        with django_assert_num_queries(1):
            meal.recipe_intakes()

    def test_get_intakes(
        self,
        meal,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        meal_recipe,
        meal_ingredients,
    ):
        expected = {
            nutrient_1.id: 0.78,
            nutrient_2.id: 10.5,
        }

        result = meal.get_intakes()

        assert result == expected

    def test_get_intakes_num_queries(
        self,
        meal,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        ingredient_nutrient_2_2,
        meal_recipe,
        meal_ingredients,
        django_assert_num_queries,
    ):
        with django_assert_num_queries(2):
            meal.get_intakes()
