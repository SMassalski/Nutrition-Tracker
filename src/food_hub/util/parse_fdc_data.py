"""Methods for parsing data from Food Data Central"""
import csv
import io
import os
from typing import List, Union

from django.conf import settings

# Loading nutrient data

UNIT_CONVERSION = {
    "MCG_RE": "UG",
    "MG_GAE": "MG",
    "MG_ATE": "MG",
}

IGNORED_UNITS = {"PH", "UMOL_TE", "SP_GR"}


def parse_nutrient_csv(nutrient_model, fp: Union[str, os.PathLike, io.IOBase] = None):
    """Read and parse FDC nutrient csv file.

    Parameters
    ----------
    nutrient_model
        The class implementing the nutrient model

    fp
        File or path to the file containing nutrient data.

    """
    if fp is None:
        fp = settings.NUTRIENT_FILE

    if isinstance(fp, io.IOBase):
        _read_nutrient_file(fp, nutrient_model)
        fp.close()
    else:
        with open(fp, newline="") as file:
            _read_nutrient_file(file, nutrient_model)


def _read_nutrient_file(file: io.IOBase, nutrient_model):
    """Read nutrient data from an open file

    Parameters
    ----------
    nutrient_model
        The class implementing the nutrient model

    file
        File or path to the file containing nutrient data.
    """
    reader = csv.DictReader(file)
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

        nutrient.save()


# Loading food data


def parse_food_csv(
    ingredient_model,
    fp: Union[str, os.PathLike, io.IOBase] = None,
    source_filter: List[str] = None,
) -> None:
    """Load FDC ids from the Foods csv file.

    Parameters
    ----------
    ingredient_model
        The class implementing the ingredient model.
    fp
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
    if fp is None:
        fp = settings.FOOD_FILE

    if isinstance(fp, io.IOBase):
        _parse_food_csv(ingredient_model, fp, source_filter)
        fp.close()
    else:
        with open(fp, newline="") as file:
            _parse_food_csv(ingredient_model, file, source_filter)


def _parse_food_csv(ingredient_model, file: io.IOBase, source_filter) -> None:
    """Load FDC ids from an open Foods csv file.

    Parameters
    ----------
    ingredient_model
        The class implementing the ingredient model.
    file
        Open file containing nutrient data.
    source_filter
        List of data sources. If not None only records from listed
        sources will be saved.
    """
    if source_filter is not None:
        source_filter = set(source_filter)

    reader = csv.DictReader(file)
    for record in reader:
        if source_filter is not None and record.get("data_type") not in source_filter:
            continue

        ingredient = ingredient_model()
        ingredient.fdc_id = int(record["fdc_id"])
        ingredient.name = record["description"]
        ingredient.dataset = record["data_type"]

        ingredient.save()
