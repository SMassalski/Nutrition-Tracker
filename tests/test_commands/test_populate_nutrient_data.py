"""Tests of the populate_nutrient_data command."""
import pytest
from django.core.management import call_command
from django.db import IntegrityError
from main import models

# noinspection PyProtectedMember
from main.management.commands._data import (
    FULL_NUTRIENT_DATA,
    NUTRIENT_TYPE_DISPLAY_NAME,
    NUTRIENT_TYPES,
)
from main.management.commands.populatenutrientdata import (
    create_energy,
    create_nutrient_components,
    create_nutrient_types,
    create_nutrients,
    create_recommendations,
    get_nutrient_types,
)

# TODO: Option to set a different data dict.

NAMES = [nut["name"] for nut in FULL_NUTRIENT_DATA]


def test_create_nutrients(db):
    """
    create_nutrients() saves to the database all specified nutrients.
    """

    create_nutrients()
    assert models.Nutrient.objects.filter(name__in=NAMES).count() == len(NAMES)


def test_create_nutrients_already_existing_nutrient(db):
    """
    create_nutrients() does not raise an exception if a nutrient that
    would be created by create_nutrients() already exists.
    """
    models.Nutrient.objects.create(name="Protein", unit="G")
    try:
        create_nutrients()
    except IntegrityError as e:
        pytest.fail(f"create_nutrients() violated a constraint - {e}")


def test_create_nutrient_types_saves_all(db):
    """
    create_nutrient_types() saves all the nutrient types in _data.
    """
    data = [
        {
            "name": "nutrient 1",
            "type": ["nutrient_type_1", "nutrient_type_2"],
        },
        {
            "name": "nutrient 2",
            "type": ["nutrient_type_1", "nutrient_type_3"],
        },
    ]
    expected = {"nutrient_type_1", "nutrient_type_2", "nutrient_type_3"}
    create_nutrient_types({}, data=data)

    nutrient_types = models.NutrientType.objects.all()
    assert {t.name for t in nutrient_types} == expected


def test_create_nutrient_types_associates_with_nutrients(db):
    """
    create_nutrient_types() associates NutrientTypes with their
    respective Nutrients.
    """
    data = [
        {
            "name": "Protein",
            "type": ["Macronutrient"],
        },
    ]
    protein = models.Nutrient.objects.create(name="Protein", unit="G")

    create_nutrient_types({"Protein": protein}, data=data)

    assert protein.types.first().name == "Macronutrient"


def test_create_nutrient_types_with_display_name(db):
    """
    create_nutrient_types() creates NutrientType records with their
    displayed names.
    """
    data = [
        {
            "name": "nutrient",
            "type": ["Fatty acid type"],
        },
    ]
    expected = NUTRIENT_TYPE_DISPLAY_NAME["Fatty acid type"]

    create_nutrient_types({}, data=data)

    displayed_name = models.NutrientType.objects.first().displayed_name
    assert displayed_name == expected


def test_create_nutrients_already_existing_nutrient_type(db):
    """
    create_nutrient_types() does not raise an exception if a nutrient
    type that would be created by create_nutrient_types() already
    exists.
    """
    protein = models.Nutrient.objects.create(name="Protein", unit="G")
    models.NutrientType.objects.create(name="Macronutrient")
    try:
        create_nutrient_types({"Protein": protein})
    except IntegrityError as e:
        pytest.fail(f"create_nutrient_types() violated a constraint - {e}")


def test_create_recommendations(db):
    """
    create_recommendations() creates recommendations for nutrients
    in `nutrient_dict`, according to the information in _data.
    """
    recommendation_data = {
        "age_max": 3,
        "age_min": 1,
        "amount_max": 20.0,
        "amount_min": 5.0,
        "dri_type": "AMDR",
        "sex": "B",
    }
    data = [{"name": "Protein", "recommendations": [recommendation_data]}]
    instance = models.Nutrient.objects.create(name="Protein", unit="G")

    create_recommendations({"Protein": instance})
    recommendation = instance.recommendations.first()

    for k, v in recommendation_data.items():
        assert getattr(recommendation, k) == v


def test_create_energy(db):
    """
    create_energy() creates NutrientEnergy records for nutrients in
    `nutrient_dict`, according to the information in _data.
    """
    expected_amount = 5
    data = [
        {
            "name": "Protein",
            "energy": expected_amount,
        }
    ]
    instance = models.Nutrient.objects.create(name="Protein", unit="G")

    create_energy({instance.name: instance}, data=data)

    assert instance.energy.amount == expected_amount


def test_create_nutrient_combinations(db):
    """
    create_nutrient_components() creates NutrientComponent records for
    nutrients in `nutrient_dict`, according to the information in
    _data.
    """
    data = [
        {
            "name": "compound",
            "unit": "MG",
            "components": ["component_1", "component_2"],
        },
        {
            "name": "component_1",
            "unit": "MG",
        },
        {
            "name": "component_2",
            "unit": "MG",
        },
    ]
    nutrients = models.Nutrient.objects.bulk_create(
        [
            models.Nutrient(name="compound", unit="MG"),
            models.Nutrient(name="component_1", unit="MG"),
            models.Nutrient(name="component_2", unit="MG"),
        ]
    )
    instance = nutrients[0]

    create_nutrient_components(
        {nutrient.name: nutrient for nutrient in nutrients}, data=data
    )

    assert instance.components.filter(name="component_1").exists()
    assert instance.components.filter(name="component_2").exists()


def test_create_nutrient_combinations_missing_component_nutrient(db):
    """
    create_nutrient_components() finishes without error despite
    a component nutrient missing from the database.
    """
    data = [
        {
            "name": "compound",
            "unit": "MG",
            "components": ["component_1", "component_2"],
        },
        {
            "name": "component_1",
            "unit": "MG",
        },
        {
            "name": "component_2",
            "unit": "MG",
        },
    ]
    nutrients = models.Nutrient.objects.bulk_create(
        [
            models.Nutrient(name="compound", unit="MG"),
            models.Nutrient(name="component_1", unit="MG"),
        ]
    )
    try:
        create_nutrient_components(
            {nutrient.name: nutrient for nutrient in nutrients}, data=data
        )
    except IntegrityError as e:
        pytest.fail(f"create_nutrient_components() violated a constraint - {e}")


def test_populate_nutrient_data_command_saves_nutrients(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrients.
    """
    call_command("populatenutrientdata")
    assert models.Nutrient.objects.filter(name__in=NAMES).count() == len(NAMES)


def test_populate_nutrient_data_command_saves_nutrient_types(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrient types.
    """
    call_command("populatenutrientdata")
    nutrient_types = models.NutrientType.objects.all()
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
    assert models.IntakeRecommendation.objects.count() == count


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
    assert models.NutrientEnergy.objects.count() == count


def test_populate_nutrient_data_command_saves_nutrient_components(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrient energies.
    """
    count = 0
    for nutrient in FULL_NUTRIENT_DATA:
        components = nutrient.get("components", None)
        if components is None:
            continue
        count += len(components)

    call_command("populatenutrientdata")
    assert models.NutrientComponent.objects.count() == count


def test_get_nutrient_types():
    """
    The get_nutrient_types() function retrieves nutrient type names
    from data in the format of FULL_NUTRIENT_DATA.
    """
    data = [
        {
            "name": "nutrient 1",
            "type": ["nutrient_type_1", "nutrient_type_2"],
        },
        {
            "name": "nutrient 2",
            "type": ["nutrient_type_1", "nutrient_type_3"],
        },
    ]
    expected = {"nutrient_type_1", "nutrient_type_2", "nutrient_type_3"}

    result = get_nutrient_types(data)

    assert result == expected
