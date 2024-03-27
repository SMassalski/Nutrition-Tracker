"""Global test fixtures."""
from datetime import date, datetime
from typing import List

import pytest
from django.test.client import Client
from main import models


@pytest.fixture
def ingredient_1(db) -> models.Ingredient:
    """Ingredient record and instance.

    name: test_ingredient
    external_id: 1
    dataset: test_dataset
    """
    name = "test_ingredient"
    external_id = 1
    dataset = "test_dataset"

    return models.Ingredient.objects.create(
        name=name, external_id=external_id, dataset=dataset
    )


@pytest.fixture
def ingredient_2(db) -> models.Ingredient:
    """Ingredient record and instance.

    name: test_ingredient_2
    external_id: 2
    dataset: test_dataset
    """
    name = "test_ingredient_2"
    external_id = 2
    dataset = "test_dataset"

    return models.Ingredient.objects.create(
        name=name, external_id=external_id, dataset=dataset
    )


@pytest.fixture
def nutrient_1(db) -> models.Nutrient:
    """Nutrient record and instance.

    name: test_nutrient
    unit: G
    energy: 0
    """
    name = "test_nutrient"
    unit = models.Nutrient.GRAMS

    return models.Nutrient.objects.create(name=name, unit=unit)


@pytest.fixture
def nutrient_2(db) -> models.Nutrient:
    """Nutrient record and instance.

    name: test_nutrient_2
    unit: UG
    energy: 0
    """
    name = "test_nutrient_2"
    unit = models.Nutrient.MICROGRAMS

    return models.Nutrient.objects.create(name=name, unit=unit)


@pytest.fixture
def ingredient_nutrient_1_1(db, ingredient_1, nutrient_1) -> models.IngredientNutrient:
    """
    IngredientNutrient associating nutrient_1 with ingredient_1.

    amount: 1.5
    """
    amount = 1.5
    return models.IngredientNutrient.objects.create(
        nutrient=nutrient_1, ingredient=ingredient_1, amount=amount
    )


@pytest.fixture
def ingredient_nutrient_1_2(ingredient_1, nutrient_2):
    """
    IngredientNutrient associating nutrient_2 with ingredient_1.

    amount: 0.1
    """
    amount = 0.1
    return models.IngredientNutrient.objects.create(
        nutrient=nutrient_2, ingredient=ingredient_1, amount=amount
    )


@pytest.fixture
def user(db) -> models.User:
    """
    A sample user record and instance.

    username: test_user
    email: test@example.com
    password: pass
    """
    return models.User.objects.create_user(
        username="test_user", email="test@example.com", password="pass"
    )


@pytest.fixture
def profile() -> models.Profile:
    """An unsaved Profile instance.

    sex: F
    age: 50
    weight: 80
    height: 180
    activity_level: LA
    energy_requirement: 2000
    """
    return models.Profile(
        sex="F",
        age=50,
        weight=80,
        height=180,
        activity_level="LA",
        energy_requirement=2000,
    )


@pytest.fixture
def saved_profile(profile, user) -> models.Profile:
    """A saved Profile instance.

    sex: F
    age: 50
    weight: 80
    height: 180
    activity_level: LA
    user: user (fixture)
    energy_requirement: 2311 (calculated)
    """
    profile.user = user
    profile.save()
    return profile


@pytest.fixture
def logged_in_client(client, user, db) -> Client:
    """Client with the user from the user fixture logged in."""
    client.force_login(user)
    return client


@pytest.fixture
def compound_nutrient(db, ingredient_1) -> models.Nutrient:
    """A sample compound nutrient.

    name: compound
    unit: G
    components:

        - name: component_1
        - unit: G
        - IngredientNutrient:
            * ingredient: ingredient_1
            * amount: 1

        - name: component_2
        - unit: G
        - IngredientNutrient:
            * ingredient: ingredient_1
            * amount: 2
    """
    nutrient = models.Nutrient.objects.create(name="compound", unit="G")
    component_1, component_2 = models.Nutrient.objects.bulk_create(
        [
            models.Nutrient(name="component_1", unit="G"),
            models.Nutrient(name="component_2", unit="G"),
        ]
    )

    models.NutrientComponent.objects.bulk_create(
        [
            models.NutrientComponent(target=nutrient, component=component_1),
            models.NutrientComponent(target=nutrient, component=component_2),
        ]
    )

    models.IngredientNutrient.objects.bulk_create(
        [
            models.IngredientNutrient(
                ingredient=ingredient_1, nutrient=component_1, amount=1
            ),
            models.IngredientNutrient(
                ingredient=ingredient_1, nutrient=component_2, amount=2
            ),
        ]
    )
    return nutrient


@pytest.fixture
def recommendation(nutrient_1) -> models.IntakeRecommendation:
    """An unsaved IntakeRecommendation instance.

    dri_type: "RDA"
    amount_min: 5.0
    amount_max: 5.0
    age_min: 0
    sex: B
    nutrient: nutrient_1
    """
    return models.IntakeRecommendation(
        dri_type=models.IntakeRecommendation.RDA,
        amount_min=5.0,
        amount_max=5.0,
        nutrient=nutrient_1,
        age_min=0,
        sex="B",
    )


@pytest.fixture
def saved_recommendation(recommendation):
    """A saved IntakeRecommendation instance.

    dri_type: "RDA"
    amount_min: 5.0
    amount_max: 5.0
    age_min: 0
    sex: B
    nutrient: nutrient_1
    """
    recommendation.save()
    return recommendation


@pytest.fixture
def meal(saved_profile) -> models.Meal:
    """A saved Meal instance.

    date: 2020-6-15
    owner: saved_profile (fixture)
    """
    return models.Meal.objects.create(owner=saved_profile, date=date(2020, 6, 15))


@pytest.fixture
def meal_ingredient(meal, ingredient_1):
    """A MealIngredient database entry and instance.

    meal: meal (fixture)
    ingredient_1: ingredient_1 (fixture)
    amount: 200
    """
    return meal.mealingredient_set.create(ingredient=ingredient_1, amount=200)


@pytest.fixture
def nutrient_1_energy(nutrient_1) -> models.Nutrient:
    """nutrient_1 with non-zero energy.

    nutrient: nutrient_1
    amount: 10
    """
    nutrient_1.energy = 10
    nutrient_1.save()
    return nutrient_1


@pytest.fixture
def nutrient_type() -> models.NutrientType:
    """A saved NutrientType without a `parent_nutrient`.

    name: "nutrient_type"
    displayed_name: "Displayed Name"
    """
    return models.NutrientType.objects.create(
        name="nutrient_type",
        displayed_name="Displayed Name",
    )


@pytest.fixture
def nutrient_1_child_type(nutrient_1):
    """A saved NutrientType with nutrient_1 as the `parent_nutrient`.

    name: "child_type"
    displayed_name: "Child Name"
    parent_nutrient: nutrient_1 (fixture)
    """
    return models.NutrientType.objects.create(
        name="child_type",
        displayed_name="Child Name",
        parent_nutrient=nutrient_1,
    )


@pytest.fixture
def nutrient_1_with_type(nutrient_1, nutrient_type):
    """nutrient_1 but with the nutrient_type added to its types.

    nutrient_1
    name: test_nutrient
    unit: G

    nutrient_type
    name: nutrient_type
    displayed_name: Displayed Name
    parent_nutrient: None
    """
    nutrient_1.types.add(nutrient_type)
    return nutrient_1


@pytest.fixture
def nutrient_2_with_type(nutrient_2, nutrient_1_child_type):
    """nutrient_2, but with the `nutrient_1_child_type` added to its
    types.

    nutrient_2
    name: test_nutrient_2
    unit: UG

    nutrient_1_child_type
    name: child_type
    displayed_name: Child Name
    parent_nutrient: nutrient_1
    """
    nutrient_2.types.add(nutrient_1_child_type)
    return nutrient_2


# Moved here because might be useful when testing views
@pytest.fixture
def many_recommendations(nutrient_1, nutrient_2) -> List[models.IntakeRecommendation]:
    """Multiple saved IntakeRecommendation instances.

    Only the first two recommendations match the profile:

    dri_type: RDA
    nutrient: nutrient_1
    age_min: 30
    age_max: 60
    sex: "B"

    dri_type: RDA
    nutrient: nutrient_2
    age_min: 0
    sex: "F"

    Three recommendations are for nutrient_1, two are for nutrient_2.
    """
    recommendations = [
        models.IntakeRecommendation(
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            age_min=30,
            age_max=60,
            sex="B",
        ),
        models.IntakeRecommendation(
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_2,
            age_min=0,
            sex="F",
        ),
        models.IntakeRecommendation(
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            age_min=0,
            sex="M",
        ),
        models.IntakeRecommendation(
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_2,
            age_min=60,
            sex="F",
        ),
        models.IntakeRecommendation(
            dri_type=models.IntakeRecommendation.RDA,
            nutrient=nutrient_1,
            age_min=0,
            age_max=10,
            sex="B",
        ),
    ]

    return models.IntakeRecommendation.objects.bulk_create(recommendations)


@pytest.fixture
def new_user(db) -> models.User:
    """Another saved user instance with a profile"""
    user = models.User.objects.create_user("name")
    profile = models.Profile(
        user=user,
        age=20,
        height=180,
        weight=80,
        activity_level=models.Profile.ACTIVE,
        sex=models.Profile.MALE,
    )
    profile.save()
    return user


@pytest.fixture
def recipe(saved_profile):
    """Recipe record and instance.

    name: test_recipe
    final_weight: 200
    """
    instance = models.Recipe(name="test_recipe", final_weight=200, owner=saved_profile)
    instance.save()
    return instance


@pytest.fixture
def recipe_ingredient(recipe, ingredient_1):
    """A RecipeIngredient entry.

    recipe: recipe
    ingredient: ingredient_1
    amount: 100
    """
    return recipe.recipeingredient_set.create(ingredient=ingredient_1, amount=100)


@pytest.fixture
def weight_measurement(saved_profile):
    """A WeightMeasurement entry.

    profile: saved_profile
    value: 80
    date: 2022-01-01
    """
    return models.WeightMeasurement.objects.create(
        profile=saved_profile, value=80, date=datetime(year=2022, month=1, day=1)
    )


@pytest.fixture
def meal_recipe(meal, recipe) -> models.MealRecipe:
    """A MealRecipe entry.

    meal: meal
    recipe: recipe
    amount: 100
    """
    return meal.mealrecipe_set.create(amount=100, recipe=recipe)


@pytest.fixture
def meal_2(ingredient_1, saved_profile):
    """Another Meal instance.

    owner: saved_profile
    date: 2020-06-01

    MealIngredient:
    ingredient: ingredient_1
    amount: 20
    """
    instance = models.Meal.objects.create(date=date(2020, 6, 1), owner=saved_profile)
    models.MealIngredient.objects.create(
        meal=instance, ingredient=ingredient_1, amount=20
    )

    return instance


@pytest.fixture
def nutrient_2_energy(nutrient_2):
    """nutrient_2 with non-zero energy.

    nutrient: nutrient_2
    amount: 4
    """
    nutrient_2.energy = 4
    nutrient_2.save()
    return nutrient_2
