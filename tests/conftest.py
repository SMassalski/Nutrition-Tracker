"""Global test fixtures."""
import pytest
from main import models


@pytest.fixture
def ingredient_1(db):
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
def ingredient_2(db):
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
def nutrient_1(db):
    """Nutrient record and instance.

    name: test_nutrient
    unit: G
    """
    name = "test_nutrient"
    unit = models.Nutrient.GRAMS

    return models.Nutrient.objects.create(name=name, unit=unit)


@pytest.fixture
def nutrient_2(db):
    """Nutrient record and instance.

    name: test_nutrient_2
    unit: UG
    """
    name = "test_nutrient_2"
    unit = models.Nutrient.MICROGRAMS

    return models.Nutrient.objects.create(name=name, unit=unit)


@pytest.fixture
def ingredient_nutrient_1_1(db, ingredient_1, nutrient_1):
    """
    IngredientNutrient associating nutrient_1 with ingredient_1.

    amount: 1.5
    """
    amount = 1.5
    return models.IngredientNutrient.objects.create(
        nutrient=nutrient_1, ingredient=ingredient_1, amount=amount
    )


@pytest.fixture
def user(db):
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
def profile():
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
def saved_profile(profile, user):
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
def logged_in_client(client, user, db):
    """Client with the user from the user fixture logged in."""
    client.force_login(user)
    return client


@pytest.fixture
def compound_nutrient(db, ingredient_1):
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
def recommendation(nutrient_1):
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
