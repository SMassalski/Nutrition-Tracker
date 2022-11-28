"""Methods for parsing data from Food Data Central"""
import io
import os
import csv
from typing import Union

from django.conf import settings

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
        try:
            _read_nutrient_file(fp, nutrient_model)
        finally:
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
