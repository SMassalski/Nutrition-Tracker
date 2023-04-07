"""Data migration loading ingredient nutrient data.

### NOTE ###
This is a very slow migration. The food_nutrient.csv is ~ 1.5 GB.
"""
# Generated by Django 4.1.3 on 2022-11-29 13:57
import csv
import io
import os
from typing import Union

from django.conf import settings
from django.db import migrations
from util import open_or_pass


def parse_food_nutrient_csv(
    file: Union[str, os.PathLike, io.IOBase],
    ingredient_nutrient_class,
    ingredient_class,
    nutrient_class,
):
    """Load per ingredient nutrient data from a food nutrient csv.

    If either the ingredient or the nutrient of a record (row) is not
    in the database the record will be skipped.

    Parameters
    ----------
    file
        File or path to the file containing nutrient data.
    ingredient_nutrient_class
        Class implementing the IngredientNutrient model.
    ingredient_class
        Class implementing the Ingredient model.
    nutrient_class
        Class implementing the Nutrient model.
    """
    # Mappings used to convert FDC ids to local ids
    nutrient_ids = {
        fdc_id: id_
        for fdc_id, id_ in nutrient_class.objects.values_list("fdc_id", "id")
    }
    ingredient_ids = {
        fdc_id: id_
        for fdc_id, id_ in ingredient_class.objects.values_list("fdc_id", "id")
    }
    ingredient_nutrient_list = []
    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:

            # Get local ids from FDC id
            ingredient_id = ingredient_ids.get(int(record.get("fdc_id")))
            nutrient_id = nutrient_ids.get(int(record.get("nutrient_id")))

            if ingredient_id is None or nutrient_id is None:
                continue

            ingredient_nutrient = ingredient_nutrient_class()
            ingredient_nutrient.ingredient_id = ingredient_id
            ingredient_nutrient.nutrient_id = nutrient_id
            ingredient_nutrient.amount = float(record["amount"])
            ingredient_nutrient_list.append(ingredient_nutrient)

    ingredient_nutrient_class.objects.bulk_create(ingredient_nutrient_list)


def parse_ingredient_nutrients(apps, schema_editor):
    """Load data from food csv (SR Legacy Food only)"""
    IngredientNutrient = apps.get_model("main", "IngredientNutrient")
    Ingredient = apps.get_model("main", "Ingredient")
    Nutrient = apps.get_model("main", "Nutrient")

    parse_food_nutrient_csv(
        settings.FOOD_NUTRIENT_FILE,
        ingredient_nutrient_class=IngredientNutrient,
        ingredient_class=Ingredient,
        nutrient_class=Nutrient,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_alter_ingredientnutrient_amount"),
    ]

    operations = [migrations.RunPython(parse_ingredient_nutrients)]
