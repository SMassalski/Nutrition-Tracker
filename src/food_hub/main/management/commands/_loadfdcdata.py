"""Helper functions for the 'loadfdcdata' command."""
import csv
import io
import os
from typing import Dict, List, Tuple, Union

from main import models

# noinspection PyProtectedMember
from main.models.foods import update_compound_nutrients
from util import get_conversion_factor, open_or_pass

from ._data import FDC_TO_NUTRIENT

# Nonstandard units and their standard counterparts.
UNIT_CONVERSION = {"MCG_RE": "UG", "MG_GAE": "MG", "MG_ATE": "MG"}

# Set of data sources in occurring in the FDC db.
# NOTE: Excluded "branded_food" and "foundation_food" to avoid more
#  complexity (not clearly indicated historical records in
#  food_nutrient.csv)
FDC_DATA_SOURCES = {
    "sr_legacy_food",
    "survey_fndds_food",
}

# NOTE:
#     Some nutrients (referred to as nonstandard nutrients) have
#     multiple records in the fdc database. If there is a record that is
#     preferred over others, the application should use the amount for
#     that record if possible.
#     These nutrients need to be treated differently:
#       - Cysteine is probably conflated with cystine in the fdc data.
#       - Vitamin A and Vitamin D can have entries in either or both IU
#       and micrograms.
#       - Vitamin B9 (Folate) has entries as total or equivalents (DFE).
#       - Vitamin K has entries that are different molecules and need
#       to be summed up.

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

# FDC IDs of the preferred FDC nutrient counterparts (if one exists)
PREFERRED_NONSTANDARD = {
    1232,  # Cysteine
    1106,  # Vitamin A, RAE
    1114,  # Vitamin D (D2 + D3)
    1177,  # Folate, total
}

VITAMIN_K_IDS = {1183, 1184, 1185}

# PARSERS


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
    Dict[int,str]
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
    dataset_filter: List[str] = None,
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

    Returns
    -------
    List[models.Ingredient]

    Notes
    -----
    FDC datasets include:
        'sr_legacy_food', 'survey_fndds_food'
    """
    data_source = models.FoodDataSource.objects.get(name="FDC")
    ingredient_list = []

    # If no dataset_filter was provided, use FDC_DATA_SOURCES that
    # contains all allowed FDC datasets
    dataset_filter = set(dataset_filter or FDC_DATA_SOURCES)

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
    """
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

            amount = float(record["amount"]) * conversion_factors[nutrient_id]

            if nutrient_id in FDC_EXCEPTION_IDS:
                handle_nonstandard(ing, nut, nutrient_id, nonstandard, amount)
                continue

            ingredient_nutrient = models.IngredientNutrient(
                ingredient=ing, nutrient=nut, amount=amount
            )
            result.append(ingredient_nutrient)

            # Batch separation
            if batch_size is not None and len(result) >= batch_size:
                models.IngredientNutrient.objects.bulk_create(result)
                result = []

    # Create IngredientNutrients from data in nonstandard.
    for ing, nutrients in nonstandard.items():
        ing_nuts = [
            models.IngredientNutrient(ingredient=ing, nutrient=nutrient, amount=amount)
            for nutrient, amount in nutrients.items()
        ]
        # Batch separation
        size = len(result) + len(ing_nuts)
        if batch_size is not None and size >= batch_size:
            models.IngredientNutrient.objects.bulk_create(result)
            result = []

        result.extend(ing_nuts)

    models.IngredientNutrient.objects.bulk_create(result)

    # Compound nutrients
    create_compound_nutrient_amounts()


# HELPERS

# TODO: Add feature to allow providing nutrient preferences
def handle_nonstandard(ingredient, nutrient, fdc_id, output_dict, amount) -> None:
    """Select the appropriate amount for a non-standard nutrient.

    Parameters
    ----------
    ingredient
    nutrient
    fdc_id
        The id of the nutrient in the FDC database.
    output_dict
        The dictionary the information will be outputted to.
    amount
        The amount of the `nutrient` in `ingredient`. The value must be
        after unit conversion.
    Returns
    -------
    None
    """
    if ingredient not in output_dict:
        output_dict[ingredient] = {}

    if nutrient not in output_dict[ingredient]:
        output_dict[ingredient][nutrient] = amount

    elif fdc_id in PREFERRED_NONSTANDARD:
        output_dict[ingredient][nutrient] = amount

    # Vitamin K
    # Summed up because vitamin K appears as 3 different molecules.
    elif fdc_id in VITAMIN_K_IDS:
        output_dict[ingredient][nutrient] += amount


def get_nutrient_conversion_factors(units: dict, nutrients: dict) -> dict:
    """Get the conversion factors needed for adding nutrient amounts.

    Nutrients in the FDC data may use different units than their
    counterparts in the app's database.
    Because of that, when adding IngredientNutrient records from FDC
    data, the amounts need to be adjusted to match local units using
    the dict from this function.

    Parameters
    ----------
    units
        A mapping from nutrient ids, in the FDC data, to its unit.
    nutrients
        A mapping from nutrient names to their instances.

    Returns
    -------
    dict
    """
    conversion_factors = {}
    for id_, unit in units.items():
        nut = nutrients.get(id_)
        if nut is not None:
            factor = get_conversion_factor(unit, nut.unit, nut.name)
            conversion_factors[id_] = factor

    return conversion_factors


class NoNutrientException(Exception):
    """
    Raised when the nutrients required for a process are not present
    in the database.
    """


def create_compound_nutrient_amounts():
    """Create IngredientNutrient instances for compound nutrients."""
    nutrients = models.Nutrient.objects.filter(components__isnull=False)
    ingredient_nutrients = []
    for nut in nutrients:
        ingredient_nutrients += update_compound_nutrients(nut, commit=False)

    models.IngredientNutrient.objects.bulk_create(
        ingredient_nutrients,
        update_conflicts=True,
        update_fields=["amount"],
        unique_fields=["ingredient", "nutrient"],
    )


def create_fdc_data_source() -> models.FoodDataSource:
    """Create a FoodDataSource record for USDA's Food Data Central."""
    return models.FoodDataSource.objects.get_or_create(name="FDC")
