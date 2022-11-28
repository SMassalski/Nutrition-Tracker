"""Tests of project utility functions"""
import csv
from io import StringIO
from typing import List, Mapping

import pytest
from util.parse_fdc_data import parse_food_csv, parse_nutrient_csv

from .dummies import DummyIngredient, DummyNutrient


@pytest.fixture
def nutrient_csv():
    """Dummy nutrient csv file and writer"""
    file = StringIO(newline="")
    writer = csv.DictWriter(
        file, fieldnames=["id", "name", "unit_name", "nutrient_nbr", "rank"]
    )
    writer.writeheader()
    yield file, writer
    file.close()


@pytest.fixture
def dummy_nutrient_class():
    """Clear DummyNutrient saved list after test."""
    yield DummyNutrient
    DummyNutrient.clear_saved()


@pytest.fixture
def food_csv():
    """Dummy sr_legacy_foods.csv file and writer"""
    file = StringIO(newline="")
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "fdc_id",
            "data_type",
            "description",
            "food_category_id",
            "publication_date",
        ],
    )
    writer.writeheader()
    yield file, writer
    file.close()


@pytest.fixture
def dummy_ingredient_class():
    """Clear DummyIngredient saved list after test."""
    yield DummyIngredient
    DummyIngredient.clear_saved()


def verify_saved_nutrient(expected: List[Mapping]) -> None:
    """Check if the saved Nutrient instances match the expected records.

    Parameters
    ----------
    expected
        List of nutrient records as they would come out of
        csv.DictReader.
    """
    assert len(expected) == len(DummyNutrient.saved)
    for record in expected:
        nutrient = DummyNutrient(
            name=record["name"], unit=record["unit_name"], fdc_id=record["id"]
        )
        assert nutrient in DummyNutrient.saved


def verify_saved_ingredients(expected: List[Mapping]) -> None:
    """Check if the saved Ingredient instances match the expected
    records.

    Parameters
    ----------
    expected
        List of ingredient records as they would come out of
        csv.DictReader.
    """
    assert len(expected) == len(DummyIngredient.saved)
    for record in expected:
        ingredient = DummyIngredient(
            name=record["description"],
            dataset=record["data_type"],
            fdc_id=record["fdc_id"],
        )

        assert ingredient in DummyIngredient.saved


def test_parse_nutrient_csv_saves_nutrients(nutrient_csv, dummy_nutrient_class):
    """parse_nutrient_csv() reads and saves nutrient records"""
    file, writer = nutrient_csv
    data = [
        {"id": 1, "name": "Carbs", "unit_name": "G", "nutrient_nbr": 200, "rank": 100},
        {
            "id": 2,
            "name": "Protein",
            "unit_name": "G",
            "nutrient_nbr": 201,
            "rank": 100,
        },
        {"id": 3, "name": "Fats", "unit_name": "G", "nutrient_nbr": 203, "rank": 100},
    ]
    writer.writerows(data)
    file.seek(0)

    parse_nutrient_csv(dummy_nutrient_class, file)
    verify_saved_nutrient(data)


def test_parse_nutrient_csv_correctly_converts_units(
    nutrient_csv, dummy_nutrient_class
):
    """
    parse_nutrient_csv() converts non-standard units to regular units.
    """
    data = [
        {
            "id": 1,
            "name": "Carbs",
            "unit_name": "MCG_RE",
            "nutrient_nbr": 200,
            "rank": 100,
        },
        {
            "id": 2,
            "name": "Protein",
            "unit_name": "MG_GAE",
            "nutrient_nbr": 201,
            "rank": 100,
        },
        {
            "id": 3,
            "name": "Fats",
            "unit_name": "MG_ATE",
            "nutrient_nbr": 203,
            "rank": 100,
        },
    ]
    file, writer = nutrient_csv
    writer.writerows(data)
    file.seek(0)

    parse_nutrient_csv(dummy_nutrient_class, file)

    data[0]["unit_name"] = "UG"
    data[1]["unit_name"] = "MG"
    data[2]["unit_name"] = "MG"

    verify_saved_nutrient(data)


def test_parse_nutrient_csv_ignores_records_with_specific_units(
    nutrient_csv, dummy_nutrient_class
):
    """
    parse_nutrient_csv() ignores records with certain units
    (usually not related to nutritional value).
    """
    data = [
        {
            "id": 1,
            "name": "Carbs",
            "unit_name": "PH",
            "nutrient_nbr": 200,
            "rank": 100,
        },
        {
            "id": 2,
            "name": "Protein",
            "unit_name": "UMOL_TE",
            "nutrient_nbr": 201,
            "rank": 100,
        },
        {
            "id": 3,
            "name": "Fats",
            "unit_name": "SP_GR",
            "nutrient_nbr": 203,
            "rank": 100,
        },
    ]
    file, writer = nutrient_csv
    writer.writerows(data)
    file.seek(0)

    parse_nutrient_csv(dummy_nutrient_class, file)
    verify_saved_nutrient([])


def test_parse_foods_csv_saves_ingredients(dummy_ingredient_class, food_csv):
    """parse_food_csv() reads and saves ingredient records"""
    file, writer = food_csv
    data = [
        dict(
            fdc_id=1,
            data_type="test_type",
            description="ingredient_1",
            food_category_id="",
            publication_date="2020-11-13",
        ),
        dict(
            fdc_id=10,
            data_type="test_type",
            description="ingredient_2",
            food_category_id="",
            publication_date="2020-11-13",
        ),
        dict(
            fdc_id=100,
            data_type="test_type_2",
            description="ingredient_3",
            food_category_id="",
            publication_date="2020-11-13",
        ),
    ]
    writer.writerows(data)
    file.seek(0)

    parse_food_csv(dummy_ingredient_class, file)
    verify_saved_ingredients(data)


def test_parse_foods_csv_filters_data_sources(dummy_ingredient_class, food_csv):
    """
    parse_food_csv() filters ingredient record based on data sources.
    """
    file, writer = food_csv
    data = [
        dict(
            fdc_id=1,
            data_type="test_type",
            description="ingredient_1",
            food_category_id="",
            publication_date="2020-11-13",
        ),
        dict(
            fdc_id=10,
            data_type="test_type",
            description="ingredient_2",
            food_category_id="",
            publication_date="2020-11-13",
        ),
        dict(
            fdc_id=100,
            data_type="test_type_2",
            description="ingredient_3",
            food_category_id="",
            publication_date="2020-11-13",
        ),
    ]
    writer.writerows(data)
    file.seek(0)

    parse_food_csv(dummy_ingredient_class, file, source_filter=["test_type"])
    verify_saved_ingredients(data[:-1])
