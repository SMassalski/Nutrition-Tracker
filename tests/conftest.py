from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir

import pytest
from django.conf import settings
from main import models


@pytest.fixture(scope="session", autouse=True)
def remove_temporary_media_dir():
    """
    Removes the test media directory if it is a temporary directory.
    """
    yield
    media_dir = Path(settings.MEDIA_ROOT)
    if Path(gettempdir()) in media_dir.parents and media_dir.exists():
        rmtree(media_dir)


@pytest.fixture(scope="session")
def ingredient_1(django_db_blocker, django_db_setup):
    """Ingredient record and instance."""
    ingredient = models.Ingredient()
    ingredient.name = "test_ingredient"
    ingredient.external_id = 1
    ingredient.dataset = "test_dataset"

    with django_db_blocker.unblock():
        ingredient.save()
    return ingredient


@pytest.fixture(scope="session")
def ingredient_2(django_db_blocker, django_db_setup):
    """Ingredient record and instance."""
    ingredient = models.Ingredient()
    ingredient.name = "test_ingredient_2"
    ingredient.external_id = 2
    ingredient.dataset = "test_dataset"

    with django_db_blocker.unblock():
        ingredient.save()
    return ingredient


@pytest.fixture(scope="session")
def nutrient_1(django_db_blocker, django_db_setup):
    """Nutrient record and instance."""
    nutrient = models.Nutrient()
    nutrient.name = "test_nutrient"
    nutrient.unit = "G"
    nutrient.external_id = 100  # Starting from 100 to avoid sharing ids with Ingredient

    with django_db_blocker.unblock():
        nutrient.save()
    return nutrient


@pytest.fixture(scope="session")
def nutrient_2(django_db_blocker, django_db_setup):
    """Nutrient record and instance."""
    nutrient = models.Nutrient()
    nutrient.name = "test_nutrient_2"
    nutrient.unit = "UG"
    nutrient.external_id = 101

    with django_db_blocker.unblock():
        nutrient.save()
    return nutrient


@pytest.fixture(scope="session")
def ingredient_nutrient_1_1(
    django_db_blocker, django_db_setup, ingredient_1, nutrient_1
):
    """
    IngredientNutrient associating nutrient_1 with ingredient_1.
    """
    instance = models.IngredientNutrient()
    instance.nutrient = nutrient_1
    instance.ingredient = ingredient_1
    instance.amount = 1.5
    with django_db_blocker.unblock():
        instance.save()
    return instance


@pytest.fixture(scope="session")
def ingredient_nutrient_1_2(
    django_db_blocker, django_db_setup, ingredient_1, nutrient_2
):
    """
    IngredientNutrient associating nutrient_2 with ingredient_1.
    """
    instance = models.IngredientNutrient()
    instance.nutrient = nutrient_2
    instance.ingredient = ingredient_1
    instance.amount = 10
    with django_db_blocker.unblock():
        instance.save()
    return instance


@pytest.fixture(scope="session")
def ingredient_nutrient_2_2(
    django_db_blocker, django_db_setup, ingredient_2, nutrient_2
):
    """
    IngredientNutrient associating nutrient_2 with ingredient_1.
    """
    instance = models.IngredientNutrient()
    instance.nutrient = nutrient_2
    instance.ingredient = ingredient_2
    instance.amount = 10
    with django_db_blocker.unblock():
        instance.save()
    return instance


@pytest.fixture(scope="session")
def user(django_db_blocker, django_db_setup):
    """
    User associating nutrient_2 with ingredient_1.
    """
    with django_db_blocker.unblock():
        instance = models.User.objects.create_user(
            "test_user", "test@example.com", "pass"
        )
    return instance


@pytest.fixture(scope="session")
def meal_component(django_db_blocker, django_db_setup, ingredient_1, ingredient_2):
    """Meal component record and instance."""
    instance = models.MealComponent(name="test_component", final_weight=200)
    with django_db_blocker.unblock():
        instance.save()
        instance.ingredients.create(ingredient=ingredient_1, amount=100)
        instance.ingredients.create(ingredient=ingredient_2, amount=100)
    return instance


@pytest.fixture()
def logged_in_client(client, user, db):
    """Client with the user from the user fixture logged in."""
    client.force_login(user)
    return client


@pytest.fixture
def compound_nutrient(db, ingredient_1):
    """A sample compound nutrient."""
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
