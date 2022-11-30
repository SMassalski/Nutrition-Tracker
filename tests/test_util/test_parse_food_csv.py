"""Tests of parse_food_csv() function"""
import csv
from io import StringIO
from typing import List, Mapping

import pytest
from util.parse_fdc_data import parse_food_csv

from tests.dummies import DummyIngredient


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


def test_parse_food_csv_saves_ingredients(dummy_ingredient_class, food_csv):
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
