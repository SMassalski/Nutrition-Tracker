"""Tests of parse_food_nutrient_csv() function"""
import csv
from io import StringIO

import pytest
from util.parse_fdc_data import parse_food_nutrient_csv


@pytest.fixture
def food_nutrient_csv():
    """Dummy food_nutrient.csv file and writer"""
    file = StringIO(newline="")
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "id",
            "fdc_id",
            "nutrient_id",
            "amount",
            "data_points",
            "derivation_id",
            "min",
            "max",
            "median",
            "loq",
            "footnote",
            "min_year_acquired",
        ],
    )
    writer.writeheader()
    yield file, writer
    file.close()


def test_parse_food_nutrient_csv_saves_ingredient_nutrients_from_csv(
    food_nutrient_csv,
    dummy_nutrient_class,
    dummy_ingredient_class,
    dummy_ingredient_nutrient_class,
):
    """parse_food_nutrient_csv() saves IngredientNutrient records"""
    file, writer = food_nutrient_csv
    data = [
        {
            "fdc_id": 10,
            "nutrient_id": 101,
            "amount": 1,
        },
        {
            "fdc_id": 10,
            "nutrient_id": 102,
            "amount": 2,
        },
        {
            "fdc_id": 11,
            "nutrient_id": 101,
            "amount": 3,
        },
    ]
    writer.writerows(data)
    file.seek(0)

    dummy_ingredient_class(
        id=1, fdc_id=10, name="ingredient_1", dataset="test_dataset"
    ).save()
    dummy_ingredient_class(
        id=2, fdc_id=11, name="ingredient_2", dataset="test_dataset"
    ).save()

    dummy_nutrient_class(id=1, fdc_id=101, name="nutrient_1", unit="G").save()
    dummy_nutrient_class(id=2, fdc_id=102, name="nutrient_1", unit="G").save()

    parse_food_nutrient_csv(
        file,
        ingredient_nutrient_class=dummy_ingredient_nutrient_class,
        ingredient_class=dummy_ingredient_class,
        nutrient_class=dummy_nutrient_class,
    )

    for record in data:
        ingredient_nutrient = dummy_ingredient_nutrient_class()
        ingredient_nutrient.ingredient_id = 1 if record["fdc_id"] == 10 else 2
        ingredient_nutrient.nutrient_id = 1 if record["nutrient_id"] == 101 else 2
        ingredient_nutrient.amount = record["amount"]

        assert ingredient_nutrient in dummy_ingredient_nutrient_class.saved


def test_parse_food_nutrient_csv_ignores_records_with_ingredients_not_in_db(
    food_nutrient_csv,
    dummy_nutrient_class,
    dummy_ingredient_class,
    dummy_ingredient_nutrient_class,
):
    """
    parse_food_nutrient_csv() ignores IngredientNutrient records
    if the ingredient is not in the database.
    """
    file, writer = food_nutrient_csv
    data = [
        {
            "fdc_id": 10,
            "nutrient_id": 101,
            "amount": 1,
        },
        {
            "fdc_id": 11,
            "nutrient_id": 101,
            "amount": 3,
        },
    ]
    writer.writerows(data)
    file.seek(0)

    dummy_ingredient_class(
        id=1, fdc_id=10, name="ingredient_1", dataset="test_dataset"
    ).save()

    dummy_nutrient_class(id=1, fdc_id=101, name="nutrient_1", unit="G").save()

    parse_food_nutrient_csv(
        file,
        ingredient_nutrient_class=dummy_ingredient_nutrient_class,
        ingredient_class=dummy_ingredient_class,
        nutrient_class=dummy_nutrient_class,
    )

    ingredient_nutrient = dummy_ingredient_nutrient_class()
    ingredient_nutrient.ingredient_id = 1
    ingredient_nutrient.nutrient_id = 1
    ingredient_nutrient.amount = 1

    assert len(dummy_ingredient_nutrient_class.saved) == 1
    assert ingredient_nutrient == dummy_ingredient_nutrient_class.saved[0]


def test_parse_food_nutrient_csv_ignores_records_with_nutrients_not_in_db(
    food_nutrient_csv,
    dummy_nutrient_class,
    dummy_ingredient_class,
    dummy_ingredient_nutrient_class,
):
    """
    parse_food_nutrient_csv() ignores IngredientNutrient records
    if the nutrient is not in the database.
    """
    file, writer = food_nutrient_csv
    data = [
        {
            "fdc_id": 10,
            "nutrient_id": 101,
            "amount": 1,
        },
        {
            "fdc_id": 10,
            "nutrient_id": 102,
            "amount": 2,
        },
    ]
    writer.writerows(data)
    file.seek(0)

    dummy_ingredient_class(
        id=1, fdc_id=10, name="ingredient_1", dataset="test_dataset"
    ).save()

    dummy_nutrient_class(id=1, fdc_id=101, name="nutrient_1", unit="G").save()

    parse_food_nutrient_csv(
        file,
        ingredient_nutrient_class=dummy_ingredient_nutrient_class,
        ingredient_class=dummy_ingredient_class,
        nutrient_class=dummy_nutrient_class,
    )

    ingredient_nutrient = dummy_ingredient_nutrient_class()
    ingredient_nutrient.ingredient_id = 1
    ingredient_nutrient.nutrient_id = 1
    ingredient_nutrient.amount = 1

    assert len(dummy_ingredient_nutrient_class.saved) == 1
    assert ingredient_nutrient == dummy_ingredient_nutrient_class.saved[0]
