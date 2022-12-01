from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir

import pytest
from django.conf import settings
from main.models import Ingredient, IngredientNutrient, Nutrient


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
    """Dummy Ingredient record and instance"""
    ingredient = Ingredient()
    ingredient.name = "test_ingredient"
    ingredient.fdc_id = 1
    ingredient.dataset = "test_dataset"

    with django_db_blocker.unblock():
        ingredient.save()
    return ingredient


@pytest.fixture(scope="session")
def ingredient_2(django_db_blocker, django_db_setup):
    """Dummy Ingredient record and instance"""
    ingredient = Ingredient()
    ingredient.name = "test_ingredient_2"
    ingredient.fdc_id = 2
    ingredient.dataset = "test_dataset"

    with django_db_blocker.unblock():
        ingredient.save()
    return ingredient


@pytest.fixture(scope="session")
def nutrient_1(django_db_blocker, django_db_setup):
    """Dummy Nutrient record and instance"""
    nutrient = Nutrient()
    nutrient.name = "test_nutrient"
    nutrient.unit = "G"
    nutrient.fdc_id = 100  # Starting from 100 to avoid sharing ids with Ingredient

    with django_db_blocker.unblock():
        nutrient.save()
    return nutrient


@pytest.fixture(scope="session")
def nutrient_2(django_db_blocker, django_db_setup):
    """Dummy Nutrient record and instance"""
    nutrient = Nutrient()
    nutrient.name = "test_nutrient_2"
    nutrient.unit = "UG"
    nutrient.fdc_id = 101

    with django_db_blocker.unblock():
        nutrient.save()
    return nutrient


@pytest.fixture(scope="session")
def ingredient_nutrient_1_1(
    django_db_blocker, django_db_setup, ingredient_1, nutrient_1
):
    """
    Dummy IngredientNutrient associating nutrient_1 with ingredient_1
    """
    instance = IngredientNutrient()
    instance.nutrient = nutrient_1
    instance.ingredient = ingredient_1
    instance.amount = 1.5
    with django_db_blocker.unblock():
        instance.save()
    return instance
