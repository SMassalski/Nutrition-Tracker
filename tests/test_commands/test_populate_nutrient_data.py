"""Tests of the populate_nutrient_data command."""
from django.core.management import call_command
from main.management.commands._data import FULL_NUTRIENT_DATA, NUTRIENT_TYPES
from main.management.commands.populatenutrientdata import (
    create_nutrient_types,
    create_nutrients,
    create_recommendations,
)
from main.models import IntakeRecommendation, Nutrient, NutrientType

NAMES = [nut["name"] for nut in FULL_NUTRIENT_DATA]


def test_create_nutrients(db):
    """
    create_nutrients() saves to the database all specified nutrients.
    """

    create_nutrients()
    assert Nutrient.objects.filter(name__in=NAMES).count() == len(NAMES)


def test_create_nutrients_already_existing_nutrient(db):
    """
    create_nutrients() does not raise an exception if a nutrient that
    would be created by create_nutrients() already exists.
    """
    Nutrient.objects.create(name="Protein", unit="G")
    create_nutrients()


def test_create_nutrient_types_saves_all(db):
    """
    create_nutrient_types() saves all the nutrient types in _data.
    """

    create_nutrient_types({})
    nutrient_types = NutrientType.objects.all()
    assert {t.name for t in nutrient_types} == NUTRIENT_TYPES


def test_create_nutrient_types_associates_with_nutrients(db):
    """
    create_nutrient_types() associates NutrientTypes with their
    respective Nutrients.
    """
    protein = Nutrient.objects.create(name="Protein", unit="G")
    create_nutrient_types({"Protein": protein})
    assert protein.types.first().name == "Macronutrient"


def test_create_recommendations(db):
    """
    create_recommendations() creates recommendations for nutrients
    in `nutrient_dict` according to the information in _data.
    """
    nutrient = FULL_NUTRIENT_DATA[0]
    name = nutrient["name"]
    instance = Nutrient.objects.create(name=name, unit=nutrient["unit"])
    create_recommendations({name: instance})
    assert instance.recommendations.count() == len(nutrient["recommendations"])


def test_populate_nutrient_data_command_saves_nutrients(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrients.
    """
    call_command("populatenutrientdata")
    assert Nutrient.objects.filter(name__in=NAMES).count() == len(NAMES)


def test_populate_nutrient_data_command_saves_nutrient_types(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrient types.
    """
    call_command("populatenutrientdata")
    nutrient_types = NutrientType.objects.all()
    assert {t.name for t in nutrient_types} == NUTRIENT_TYPES


def test_populate_nutrient_data_command_saves_intake_recommendations(db):
    """
    The populate_nutrient_data command saves to the database all
    specified intake recommendations.
    """
    count = 0
    for nutrient in FULL_NUTRIENT_DATA:
        count += len(nutrient["recommendations"])

    call_command("populatenutrientdata")
    assert IntakeRecommendation.objects.count() == count
