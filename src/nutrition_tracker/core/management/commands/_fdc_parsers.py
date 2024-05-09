"""Parsing functions used by the `loadfdcdata` command.

Notes
-----
Some nutrients (referred to as nonstandard nutrients) have
multiple records in the fdc database. If there is a record that is
preferred over others, the application should use the amount for
that record if possible.
These nutrients need to be treated differently:
  - Cysteine is probably conflated with cystine in the fdc data.
  - Vitamin A and Vitamin D can have entries in either or both IU
  and micrograms.
  - Vitamin B9 (Folate) has entries as total or equivalents (DFE).
  - Vitamin K has entries that are different molecules and need
  to be summed up.
"""
import csv
import io
import os
from typing import Dict, List, Tuple, Union

from core import models
from util import open_or_pass

from ._data import FDC_TO_NUTRIENT
from ._fdc_helpers import (
    NoNutrientException,
    create_compound_nutrient_amounts,
    get_nutrient_conversion_factors,
    handle_nonstandard,
)

# Nonstandard units and their standard counterparts.
UNIT_CONVERSION = {"MCG_RE": "UG", "MG_GAE": "MG", "MG_ATE": "MG"}

# Set of data sources in occurring in the FDC db.
# Excluded "branded_food" and "foundation_food" to avoid more
# complexity (not clearly indicated historical records in
# food_nutrient.csv)
FDC_DATASETS = {
    "sr_legacy_food",
    "survey_fndds_food",
}


# IDs in the FDC db of nutrients that have to be treated differently.
FDC_EXCEPTION_IDS = {
    # Cysteine
    1216,
    1232,
    # Vitamin A
    1104,
    1106,
    # Vitamin D
    1110,
    1114,
    # Vitamin B9 (Folate)
    1177,
    1190,
    # Vitamin K
    1183,
    1184,
    1185,
}


def parse_nutrient_csv(
    file: Union[str, os.PathLike, io.IOBase]
) -> Tuple[Dict[int, str], Dict[str, int]]:
    """Retrieve nutrient unit and nbr from the FDC nutrient.csv file.

    Parameters
    ----------
    file
        File or path to the file containing nutrient data.

    Returns
    -------
    Dict[int, str]
        Mapping of nutrient's id to its unit in FDC data.
    Dict[str, int]
        Mapping of nutrient_nbr to id in FDC data.
    """
    units = {}
    nbr_to_id = {}
    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for nutrient_record in reader:
            unit = nutrient_record.get("unit_name")
            id_ = int(nutrient_record.get("id"))

            # Map nutrient's FDC id to it's unit
            units[id_] = UNIT_CONVERSION.get(unit) or unit
            nbr_to_id[nutrient_record.get("nutrient_nbr")] = id_

    return units, nbr_to_id


def parse_food_csv(
    file: Union[str, os.PathLike, io.IOBase],
    dataset_filter: List[str],
    data_source: models.FoodDataSource,
) -> List[models.Ingredient]:
    """Load ingredient data from the Foods csv file.

    Parameters
    ----------
    file
        File or path to the file containing nutrient data.
    dataset_filter
        List of data sources.
        If `dataset_filter` is not None only records from listed
        sources are saved.
    data_source
        The FDC data source.

    Returns
    -------
    List[models.Ingredient]

    Raises
    ------
    ValueError
        Raised if `dataset_filter` includes an unrecognized dataset
        name.

    Notes
    -----
    Allowed FDC datasets include:
        'sr_legacy_food', 'survey_fndds_food'
    """
    for dataset in dataset_filter:
        if dataset not in FDC_DATASETS:
            raise ValueError(f"Unrecognized dataset: {dataset}")

    ingredient_list = []

    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:
            # Filtering data sources
            if record.get("data_type") not in dataset_filter:
                continue

            ingredient = models.Ingredient()
            ingredient.external_id = int(record["fdc_id"])
            ingredient.name = record["description"]
            ingredient.dataset = record["data_type"]
            ingredient.data_source = data_source

            ingredient_list.append(ingredient)

    return ingredient_list


def parse_food_nutrient_csv(
    file: Union[str, os.PathLike, io.IOBase],
    nutrient_file: Union[str, os.PathLike, io.IOBase],
    batch_size: int = None,
    preferred_nutrients: "collections.abc.Container" = None,
    additive_nutrients: "collections.abc.Container" = None,
) -> None:
    """Load per ingredient nutrient data from a food_nutrient.csv file.

    If either the ingredient or the nutrient of a record (row) is not
    in the database, the record will be skipped.

    Parameters
    ----------
    file
        File or path to the file containing ingredient nutrient data.
    nutrient_file
        File or path to the containing nutrient data.
    batch_size
        The max number of IngredientNutrient records to save per batch.
        If `None` saves all records in a single batch. Helps with memory
        limitations.
    preferred_nutrients
        The FDC ids of nutrient records to be used over other records
        of the same nutrient.
        This is used to deal with situations where one ingredient has
        amount values for multiple nutrient records.
    additive_nutrients
        The FDC ids of additive nutrients.
        See `_fdc_helpers.handle_nonstandard` for a definition.
    """
    preferred_nutrients = preferred_nutrients or tuple()
    additive_nutrients = additive_nutrients or tuple()

    nutrients = models.Nutrient.objects.filter(name__in=FDC_TO_NUTRIENT.values())
    if not nutrients.exists():
        raise NoNutrientException("No nutrients found.")

    # Mapping of FDC nutrient ids to this app's nutrient instances.
    nutrients = {n.name: n for n in nutrients}
    nutrients = {
        id_: nutrients[name]
        for id_, name in FDC_TO_NUTRIENT.items()
        if name in nutrients
    }

    units, nutrient_nbr_id = parse_nutrient_csv(nutrient_file)
    conversion_factors = get_nutrient_conversion_factors(units, nutrients)

    # Mappings from FDC ids to ingredient instances.
    ingredient_ids = {}
    for ing in models.Ingredient.objects.filter(data_source__name="FDC"):
        ingredient_ids[ing.external_id] = ing

    result = []  # List of created IngredientNutrients instances
    nonstandard = {}  # Data for nonstandard nutrients

    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:

            # Get instances and final amount.
            ing = ingredient_ids.get(int(record.get("fdc_id")))

            # Some food_nutrient records refer to the nutrient number
            # instead of id (FDDNS specifically).
            nutrient_id = record.get("nutrient_id")
            nutrient_id = nutrient_nbr_id.get(nutrient_id, int(nutrient_id))
            nut = nutrients.get(nutrient_id)

            # Skip if either ingredient or nutrient is not in DB.
            if ing is None or nut is None:
                continue

            # Divided by 100 because the amounts in the FDC data are
            # stored in <unit> per 100 g.
            amount = float(record["amount"]) * conversion_factors[nutrient_id] / 100

            if nutrient_id in FDC_EXCEPTION_IDS:
                handle_nonstandard(
                    ing,
                    nut,
                    nutrient_id,
                    nonstandard,
                    amount,
                    preferred_nutrients=preferred_nutrients,
                    additive_nutrients=additive_nutrients,
                )
                continue

            ingredient_nutrient = models.IngredientNutrient(
                ingredient=ing, nutrient=nut, amount=amount
            )
            result.append(ingredient_nutrient)

            # Batch separation
            if batch_size is not None and len(result) >= batch_size:
                models.IngredientNutrient.objects.bulk_create(result)
                result = []

    models.IngredientNutrient.objects.bulk_create(result)

    create_ingredient_nutrients_from_dict(nonstandard, batch_size)

    # Compound nutrients
    create_compound_nutrient_amounts()


def create_ingredient_nutrients_from_dict(
    data: dict, batch_size: int = None
) -> List[models.IngredientNutrient]:
    """Create and save IngredientNutrients from `data`.

    Parameters
    ----------
    data
        The data from which to create IngredientNutrient instances.
        `data` has the format {ingredient: {nutrient: amount}}
        where ingredient and nutrient are instances of the Ingredient
        and Nutrient model respectively, and amount is the amount of the
        nutrient in the ingredient

    batch_size
        The min size of batches in which the created IngredientNutrients
        are saved to the database.
        If `batch_size` is not None, the instances will be saved to the
        database in batches of size at least `batch_size`.

    Returns
    -------
    List[models.IngredientNutrient]

    Raises
    ------
    ValueError
        Raised when batch_size is less than 1.
    """
    if batch_size is not None and batch_size < 1:
        raise ValueError("batch size must be a positive integer greater than 0")

    result = []
    for ing, nutrients in data.items():
        ing_nuts = [
            models.IngredientNutrient(ingredient=ing, nutrient=nut, amount=amount)
            for nut, amount in nutrients.items()
        ]
        # Batch separation
        size = len(result) + len(ing_nuts)
        if batch_size is not None and size >= batch_size:
            models.IngredientNutrient.objects.bulk_create(result)
            result = []

        result.extend(ing_nuts)
    models.IngredientNutrient.objects.bulk_create(result)
