"""Tests of parse_nutrient_csv() function"""
import csv
from io import StringIO
from typing import List, Mapping

import pytest
from util.parse_fdc_data import parse_nutrient_csv

from ..dummies import DummyNutrient


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
