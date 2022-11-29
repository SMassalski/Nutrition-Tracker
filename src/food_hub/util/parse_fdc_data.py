"""Methods for parsing data from Food Data Central"""
import csv
import io
import os
from typing import List, Union

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

            nutrient.save()


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
    with _open_or_pass(file, newline="") as f:
        if source_filter is not None:
            source_filter = set(source_filter)

        reader = csv.DictReader(f)
        for record in reader:
            if (
                source_filter is not None
                and record.get("data_type") not in source_filter
            ):
                continue

            ingredient = ingredient_model()
            ingredient.fdc_id = int(record["fdc_id"])
            ingredient.name = record["description"]
            ingredient.dataset = record["data_type"]

            ingredient.save()


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
