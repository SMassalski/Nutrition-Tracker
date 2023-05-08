"""Tests of ORM models"""
from datetime import datetime

import pytest
from main import models


@pytest.fixture()
def ingredient_1_macronutrients(db, ingredient_1):
    protein = models.Nutrient.objects.create(name="Protein")
    fat = models.Nutrient.objects.create(name="Total lipid (fat)")
    carbs = models.Nutrient.objects.create(name="Carbohydrate, by difference")

    models.IngredientNutrient.objects.bulk_create(
        [
            models.IngredientNutrient(
                ingredient_id=ingredient_1.id, nutrient_id=protein.id, amount=1
            ),
            models.IngredientNutrient(
                ingredient_id=ingredient_1.id, nutrient_id=fat.id, amount=2
            ),
            models.IngredientNutrient(
                ingredient_id=ingredient_1.id, nutrient_id=carbs.id, amount=3
            ),
        ]
    )

    return ingredient_1.macronutrient_calories


# Ingredient model
def test_ingredient_string_representation():
    """Ingredient model's string representation is its name"""
    ingredient = models.Ingredient(dataset="test_dataset", name="test_name")
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


def test_ingredient_macronutrient_calories_returns_only_3_macronutrients(
    ingredient_1_macronutrients,
):
    """
    Ingredient.macronutrient_calories returns values only for protein
    fat and carbohydrates.
    """
    result = ingredient_1_macronutrients
    assert len(result.keys()) == 3
    for macronutrient in ["carbohydrate", "lipid", "protein"]:
        assert len([k for k in result.keys() if macronutrient in k.lower()]) == 1


def test_ingredient_macronutrient_calories_converts_nutrients_to_calories_correctly(
    ingredient_1_macronutrients,
):
    """
    Ingredient.macronutrient_calories calculates calorie amounts
    according to atwater conversion factors (4 kcal/g for protein and
    carbs, 9 kcal/g for fats).
    """
    # Values depend on amounts in ingredient_1_macronutrients
    assert ingredient_1_macronutrients == {
        "Protein": 4,
        "Total lipid (fat)": 18,
        "Carbohydrate, by difference": 12,
    }


def test_ingredient_macronutrient_calories_returns_a_dict_sorted_by_keys(
    ingredient_1_macronutrients,
):
    """
    Ingredient.macronutrient_calories calculates return dict is sorted
    by keys.
    """
    assert ingredient_1_macronutrients == dict(
        sorted(ingredient_1_macronutrients.items())
    )


# Nutrient model
def test_nutrient_string_representation():
    """
    Nutrient model's string representation follows the format
    <name> (<pretty unit symbol>).
    """
    nutrient = models.Nutrient(name="test_name", unit="UG")
    assert (
        str(nutrient)
        == f"{nutrient.name} ({models.Nutrient.PRETTY_UNITS[nutrient.unit]})"
    )


def test_save_updates_amounts_from_db(db, ingredient_1):
    """
    Updating a nutrient's unit changes the amount value of related
    IngredientNutrient records so that the actual amount remains
    unchanged. Test for when the instance was loaded from the database.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient = models.Nutrient.objects.get(pk=nutrient.id)
    nutrient.unit = "MG"
    nutrient.save()

    ing_nut.refresh_from_db()

    assert ing_nut.amount == 1000


def test_save_updates_amounts_created(db, ingredient_1):
    """
    Updating a nutrient's unit changes the amount value of related
    IngredientNutrient records so that the actual amount remains
    unchanged. Test for when the instance was created and saved.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient.unit = "MG"
    nutrient.save()

    ing_nut.refresh_from_db()

    assert ing_nut.amount == 1000


def test_save_updates_amounts_from_db_deferred(db, ingredient_1):
    """
    Updating a nutrient's unit changes the amount value of related
    IngredientNutrient records so that the actual amount remains
    unchanged. Test for when the instance was loaded from the database,
    but the unit field was deferred.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient = models.Nutrient.objects.defer("unit").get(id=nutrient.id)
    nutrient.unit = "MG"
    nutrient.save()

    ing_nut.refresh_from_db()

    assert ing_nut.amount == 1000


def test_save_update_amounts_false(db, ingredient_1):
    """
    Updating a nutrient's unit doesn't change the amount value of related
    IngredientNutrient records if save was called with `update_amounts`
    set to False.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient.unit = "MG"
    nutrient.save(update_amounts=False)

    assert ing_nut.amount == 1


# Meal Component model
def test_meal_component_string_representation():
    """MealComponent model's string representation is its name"""
    assert (
        str(models.MealComponent(name="test_meal_component")) == "test_meal_component"
    )


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
    ingredient = models.Ingredient(name="test_ingredient")
    component = models.MealComponent(name="test_component")
    meal_component_ingredient = models.MealComponentIngredient(
        ingredient=ingredient, meal_component=component
    )
    assert str(meal_component_ingredient) == "test_component - test_ingredient"


# Meal model
def test_meal_string_representation():
    """
    Meal model's string representation is its name and formatted date.
    """
    meal = models.Meal(
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


# Profile model tests
# The initialism EER refers to "estimated energy requirement"


def test_profile_string_representation(db):
    """
    Profile model's string representation follows the format of
    `<associated user's username>'s profile`.
    """
    user = models.User.objects.create_user(username="profile_test_user")
    profile = models.Profile(user=user)

    assert str(profile) == "profile_test_user's profile"


def test_profile_energy_calculation_for_a_man():
    """
    Profile's calculate energy method correctly calculates the EER of
    an adult male.
    """
    profile = models.Profile(
        age=35, weight=80, height=180, sex="M", activity_level="LA"
    )
    assert profile.calculate_energy() == 2819


def test_profile_energy_calculation_for_a_woman():
    """
    Profile's calculate energy method correctly calculates the EER of
    an adult female.
    """
    profile = models.Profile(age=35, weight=60, height=170, sex="F", activity_level="A")
    assert profile.calculate_energy() == 2393


def test_profile_energy_calculation_for_a_boy():
    """
    Profile's calculate energy method correctly calculates the EER of
    a non-adult male.
    """
    profile = models.Profile(age=15, weight=50, height=170, sex="M", activity_level="S")
    assert profile.calculate_energy() == 2055


def test_profile_energy_calculation_for_a_girl():
    """
    Profile's calculate energy method correctly calculates the EER of
    a non-adult female.
    """
    profile = models.Profile(age=6, weight=35, height=140, sex="F", activity_level="A")
    assert profile.calculate_energy() == 2142


def test_profile_energy_calculation_for_a_2_yo():
    """
    Profile's calculate energy method correctly calculates the EER of
    a 2-year-old child.
    """
    profile = models.Profile(age=2, weight=12, height=140, sex="F", activity_level="A")
    assert profile.calculate_energy() == 988


def test_profile_energy_calculation_for_a_lt_1_yo():
    """
    Profile's calculate energy method correctly calculates the EER of
    a 1-year-old child.
    """
    profile = models.Profile(age=0, weight=9, height=140, sex="F", activity_level="A")
    assert profile.calculate_energy() == 723


def test_profile_create_calculates_energy(db, user):
    """Saving a new profile record automatically calculates the EER."""
    profile = models.Profile(
        age=35, weight=80, height=180, sex="M", activity_level="LA", user=user
    )
    profile.save()
    profile.refresh_from_db()
    assert profile.energy_requirement == 2819


def test_profile_update_calculates_energy(db, user):
    """Updating a profile record automatically calculates the EER."""
    profile = models.Profile(
        age=35, weight=80, height=180, sex="M", activity_level="LA", user=user
    )
    profile.save()
    profile.weight = 70
    profile.save()
    profile.refresh_from_db()
    assert profile.energy_requirement == 2643


def test_food_data_source_string_representation():
    """
    The string representation of a FoodDataSource instance is its name.
    """
    assert str(models.FoodDataSource(name="test_name")) == "test_name"
