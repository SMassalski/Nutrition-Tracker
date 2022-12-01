"""Methods for parsing data from Food Data Central."""
import csv
import io
import os
from typing import List, Union

from main.models import Ingredient, IngredientNutrient, Nutrient

# Parsing functions require providing model classes for migration
# compatibility and easier testing with fakes.

# Loading nutrient data

UNIT_CONVERSION = {
    "MCG_RE": "UG",
    "MG_GAE": "MG",
    "MG_ATE": "MG",
}

IGNORED_UNITS = {"PH", "UMOL_TE", "SP_GR"}


def parse_nutrient_csv(nutrient_model, file: Union[str, os.PathLike, io.IOBase]):
    """Read and parse FDC nutrient csv file.

    Parameters
    ----------
    nutrient_model
        The class implementing the nutrient model

    file
        File or path to the file containing nutrient data.

    """
    nutrient_list = []
    with _open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for nutrient_record in reader:

            # Unit parsing
            unit = nutrient_record.get("unit_name")
            if unit in IGNORED_UNITS:
                continue
            unit = UNIT_CONVERSION.get(unit) or unit

            nutrient = nutrient_model()
            nutrient.unit = unit
            nutrient.name = nutrient_record.get("name")
            nutrient.fdc_id = int(nutrient_record.get("id"))

            nutrient_list.append(nutrient)
    nutrient_model.objects.bulk_create(nutrient_list)


# Loading food data


def parse_food_csv(
    ingredient_model,
    file: Union[str, os.PathLike, io.IOBase],
    source_filter: List[str] = None,
) -> None:
    """Load ingredient data from the Foods csv file.

    Parameters
    ----------
    ingredient_model
        The class implementing the ingredient model.
    file
        File or path to the file containing nutrient data.
    source_filter
        List of data sources. If not None only records from listed
        sources will be saved.

    Notes
    -----
    Data sources include:
        'branded_food', 'experimental_food', 'sr_legacy_food',
        'sample_food', 'market_acquistion', 'sub_sample_food',
        'foundation_food', 'agricultural_acquisition',
        'survey_fndds_food'
    """
    ingredient_list = []
    with _open_or_pass(file, newline="") as f:
        if source_filter is not None:
            source_filter = set(source_filter)

        reader = csv.DictReader(f)
        for record in reader:

            # Filtering data sources
            if (
                source_filter is not None
                and record.get("data_type") not in source_filter
            ):
                continue

            ingredient = ingredient_model()
            ingredient.fdc_id = int(record["fdc_id"])
            ingredient.name = record["description"]
            ingredient.dataset = record["data_type"]

            ingredient_list.append(ingredient)

    ingredient_model.objects.bulk_create(ingredient_list)


def parse_food_nutrient_csv(
    file: Union[str, os.PathLike, io.IOBase],
    ingredient_nutrient_class=IngredientNutrient,
    ingredient_class=Ingredient,
    nutrient_class=Nutrient,
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
    with _open_or_pass(file, newline="") as f:
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


def _open_or_pass(file: Union[str, os.PathLike, io.IOBase], *args, **kwargs):
    """Open a file if `file` is a path.

    If `file` is an instance of a subclass of io.IOBase the function
    returns the `file` unchanged.

    Parameters
    ----------
    file
        File or path to the file to be opened.
    args
        Positional arguments passed to open() if used.
    kwargs
        Keyword arguments passed to open() if used.
    Returns
    -------
    io.IOBase
        The open file.
    """
    if isinstance(file, io.IOBase):
        return file
    return open(file, *args, **kwargs)
