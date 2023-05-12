"""Helper functions for the 'populatefdcdata' command."""
import csv
import io
import os
from typing import Dict, List, Tuple, Union

from main import models
from main.management.commands.populatenutrientdata import NoNutrientException
from util import get_conversion_factor, open_or_pass

# Nonstandard units and their standard counterparts.
UNIT_CONVERSION = {
    "MCG_RE": "UG",
    "MG_GAE": "MG",
    "MG_ATE": "MG",
}

# Mapping of nutrient's ID in the FDC database to the nutrient's name in
# this application.
FDC_TO_NUTRIENT = {
    1003: "Protein",
    1004: "Lipid",
    1005: "Carbohydrate",
    1007: "Ash",
    1008: "Energy",
    1051: "Water",
    1079: "Fiber",
    1087: "Calcium",
    1088: "Chlorine",
    1089: "Iron",
    1090: "Magnesium",
    1091: "Phosphorus",
    1092: "Potassium",
    1093: "Sodium",
    1095: "Zinc",
    1096: "Chromium",
    1098: "Copper",
    1099: "Fluoride",
    1100: "Iodine",
    1101: "Manganese",
    1102: "Molybdenum",
    1103: "Selenium",
    1104: "Vitamin A",
    1106: "Vitamin A",
    1109: "Vitamin E",
    1110: "Vitamin D",
    1111: "Vitamin D2",
    1112: "Vitamin D3",
    1114: "Vitamin D",
    1134: "Arsenic",
    1137: "Boron",
    1146: "Nickel",
    1150: "Silicon",
    1155: "Vanadium",
    1162: "Vitamin C",
    1165: "Vitamin B1",
    1166: "Vitamin B2",
    1167: "Vitamin B3",
    1170: "Vitamin B5",
    1175: "Vitamin B6",
    1176: "Vitamin B7",
    1177: "Vitamin B9",
    1178: "Vitamin B12",
    1183: "Vitamin K",
    1184: "Vitamin K",
    1185: "Vitamin K",
    1190: "Vitamin B9",
    1210: "Tryptophan",
    1211: "Threonine",
    1212: "Isoleucine",
    1213: "Leucine",
    1214: "Lysine",
    1215: "Methionine",
    1216: "Cysteine",
    1217: "Phenylalanine",
    1218: "Tyrosine",
    1219: "Valine",
    1220: "Arginine",
    1221: "Histidine",
    1222: "Alanine",
    1223: "Aspartic acid",
    1224: "Glutamic acid",
    1225: "Glycine",
    1226: "Proline",
    1227: "Serine",
    1231: "Asparagine",
    1232: "Cysteine",
    1233: "Glutamine",
    1253: "Cholesterol",
    1257: "Trans fatty acids",
    1258: "Saturated fatty acids",
    1292: "Monounsaturated fatty acids",
    1293: "Polyunsaturated fatty acids",
    2000: "Sugars",
    1235: "Sugars (added)",
    1404: "alpha-Linolenic acid",
    1316: "Linoleic acid",
    1180: "Choline",
}

# Set of data sources in occurring in the FDC db.
# NOTE: Excluded "experimental_food", "sample_food", "market_acquistion",
#  "sub_sample_food", "agricultural_acquisition" (multiple records for a
#  single ingredient).
#  "branded_food" and "foundation_food" to avoid more complexity
#  (not clearly indicated historical records in food_nutrient.csv)
FDC_DATA_SOURCES = {
    "sr_legacy_food",
    "survey_fndds_food",
}

# NOTE:
#     Some nutrients (referred to as nonstandard nutrients) have
#     multiple records in the fdc database. If there is a record that is
#     preferred over others the application should use the amount for
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


def create_fdc_data_source() -> models.FoodDataSource:
    """Create a FoodDataSource record for USDA's Food Data Central."""
    return models.FoodDataSource.objects.get_or_create(name="FDC")


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
        List of data sources. If not None only records from listed
        sources will be saved.

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

    # If no dataset_filter was provided use FDC_DATA_SOURCES that
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
    in the database the record will be skipped.

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
    # Raise exception if nutrients in FDC_TO_NUTRIENT are not in the DB
    if not nutrients.exists():
        raise NoNutrientException("No nutrients found.")

    # Mapping of FDC nutrient ids to this app's nutrient instances.
    nutrients = {n.name: n for n in nutrients}
    nutrients = {
        id_: nutrients[name]
        for id_, name in FDC_TO_NUTRIENT.items()
        if name in nutrients
    }

    # Mapping of FDC id of nutrients to the conversion factor to be used
    # when setting the nutrient's amount in ingredient.
    units, nutrient_nbr_id = parse_nutrient_csv(nutrient_file)
    conversion_factors = {}
    for id_, unit in units.items():
        nut = nutrients.get(id_)
        if nut is not None:
            factor = get_conversion_factor(unit, nut.unit, nut.name)
            conversion_factors[id_] = factor

    # Mappings used to convert FDC ids to ingredients.
    ingredient_ids = {}
    for ing in models.Ingredient.objects.filter(data_source__name="FDC"):
        ingredient_ids[ing.external_id] = ing

    result = []  # List of created (not saved) IngredientNutrients
    nonstandard = {}  # Data for nonstandard nutrients

    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:

            # Get instances and final amount.
            ing = ingredient_ids.get(int(record.get("fdc_id")))
            nutrient_id = record.get("nutrient_id")  # FDC nutrient id

            # Check if record refers to nutrient_nbr or id.
            # Some food_nutrient records refer to the nutrient number
            # instead of id (FDDNS specifically).
            nutrient_id = nutrient_nbr_id.get(nutrient_id, int(nutrient_id))
            nut = nutrients.get(nutrient_id)

            # Skip if either ingredient or nutrient is not in DB.
            if ing is None or nut is None:
                continue

            # Grab amount and convert units if necessary
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


def handle_nonstandard(ingredient, nutrient, fdc_id, output_dict, amount) -> None:
    """Select the appropriate amount for a non-standard nutrient.

    Parameters
    ----------
    ingredient
    nutrient
    fdc_id
        The id of the nutrient in th FDC database.
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

    # Prefer Cysteine (FDC_ID: 1232) over Cystine (FDC_ID: 1216)
    # Prefer Vitamin A, RAE (1106) over Vitamin A, IU (1104)
    # Prefer Vitamin D (D2 + D3) (1114)
    #   over Vitamin D (D2 + D3), International Units (1110)
    # Prefer Folate, total (1177) over Folate, DFE (1190)
    elif fdc_id in PREFERRED_NONSTANDARD:
        output_dict[ingredient][nutrient] = amount

    # Vitamin K
    # Summed up because vitamin K appears as 3 different molecules.
    elif fdc_id in {1183, 1184, 1185}:
        output_dict[ingredient][nutrient] += amount
