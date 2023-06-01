"""Tests of the populate_nutrient_data command."""
import pytest
from django.core.management import call_command
from django.db import IntegrityError
from main.management.commands._data import (
    FULL_NUTRIENT_DATA,
    NUTRIENT_TYPE_DISPLAY_NAME,
    NUTRIENT_TYPES,
)
from main.management.commands.populatenutrientdata import (
    create_energy,
    create_nutrient_types,
    create_nutrients,
    create_recommendations,
)
from main.models import IntakeRecommendation, Nutrient, NutrientEnergy, NutrientType

# TODO: Option to set a different data dict.

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
    try:
        create_nutrients()
    except IntegrityError as e:
        pytest.fail(f"create_nutrients() violated a constraint - {e}")


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


def test_create_nutrient_types_with_display_name(db):
    """
    create_nutrient_types() creates NutrientType records with their
    displayed names.
    """
    create_nutrient_types({})
    types = NutrientType.objects.filter(name__in=NUTRIENT_TYPE_DISPLAY_NAME).values()
    for t in types:
        assert NUTRIENT_TYPE_DISPLAY_NAME[t["name"]] == t["displayed_name"]


def test_create_nutrients_already_existing_nutrient_type(db):
    """
    create_nutrient_types() does not raise an exception if a nutrient
    type that would be created by create_nutrient_types() already
    exists.
    """
    protein = Nutrient.objects.create(name="Protein", unit="G")
    NutrientType.objects.create(name="Macronutrient")
    try:
        create_nutrient_types({"Protein": protein})
    except IntegrityError as e:
        pytest.fail(f"create_nutrient_types() violated a constraint - {e}")


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


def test_create_energy(db):
    """
    create_energy() creates NutrientEnergy records for nutrients in
    `nutrient_dict` according to the information in _data.
    """
    # Protein 4 kcal/g
    instance = Nutrient.objects.create(name="Protein", unit="G")
    create_energy({instance.name: instance})
    assert instance.energy.amount == 4


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


def test_populate_nutrient_data_command_saves_nutrient_energy(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrient energies.
    """
    count = 0
    for nutrient in FULL_NUTRIENT_DATA:
        if nutrient.get("energy", False):
            count += 1

    call_command("populatenutrientdata")
    assert NutrientEnergy.objects.count() == count
