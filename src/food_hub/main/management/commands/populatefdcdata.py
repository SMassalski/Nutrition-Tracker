"""
Command and helper functions for populating the database with data
from Food Data Central csv files.
"""
import csv
import io
import os
from pathlib import Path
from typing import Dict, List, Union

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from main import models
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
    1257: "Trans fatty acid",
    1258: "Saturated fatty acids",
    1292: "Monounsaturated fatty acids",
    1293: "Polyunsaturated fatty acids",
    2000: "Sugars",
}

# Set of data sources in occurring in the FDC db.
FDC_DATA_SOURCES = {
    "branded_food",
    "experimental_food",
    "sr_legacy_food",
    "sample_food",
    "market_acquistion",
    "sub_sample_food",
    "foundation_food",
    "agricultural_acquisition",
    "survey_fndds_food",
}

# NOTE:
#     Some nutrients have multiple records in the fdc
#     database. If there is a record that is preferred over others
#     the application should use the amount for that record if
#     possible.
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
PREFERRED_NON_STANDARD = {
    1232,  # Cysteine
    1106,  # Vitamin A, RAE
    1114,  # Vitamin D (D2 + D3)
    1177,  # Folate, total
}


class Command(BaseCommand):
    """Populate the database with data from FDC csv files."""

    help = (
        "Populates the database with data from Food Data Central csv files. "
        "By default the command looks for the files in the directory indicated by "
        "the DATA_DIR setting."
    )

    # docstr-coverage: inherited
    def add_arguments(self, parser):
        parser.add_argument(
            "--data_dir", type=str, help="Directory where the data files are located."
        )
        parser.add_argument(
            "--food_file",
            type=str,
            help="Path to the file containing food data (food.csv). Overrides data_dir"
            " discovery.",
        )
        parser.add_argument(
            "--nutrient_file",
            type=str,
            help="Path to the file containing nutrient data (nutrient.csv). Overrides "
            "data_dir discovery.",
        )
        parser.add_argument(
            "--food_nutrient_file",
            type=str,
            help="Path to the file containing food nutrient data (food_nutrient.csv). "
            "Overrides data_dir discovery.",
        )
        parser.add_argument(
            "--dataset_filter",
            nargs="+",
            type=str,
            help="If provided only saves food records from specified FDC datasets. "
            "Available datasets: "
            "'branded_food', 'experimental_food', 'sr_legacy_food',"
            "'sample_food', 'market_acquistion', 'sub_sample_food',"
            "'foundation_food', 'agricultural_acquisition',"
            "'survey_fndds_food'",
        )

    # docstr-coverage: inherited
    def handle(self, *args, **options):

        # Selecting file paths from config
        try:
            data_dir = Path(options["data_dir"] or settings.DATA_DIR)
        except AttributeError:
            data_dir = None

        if data_dir is None:
            try:
                # Check if the user provided each file individually
                food_file = Path(options["food_file"])
                nutrient_file = Path(options["nutrient_file"])
                food_nutrient_file = Path(options["food_nutrient_file"])
            except TypeError:
                no_path = []
                if not options["food_file"]:
                    no_path.append("food.csv")
                if not options["nutrient_file"]:
                    no_path.append("nutrient.csv")
                if not options["food_nutrient_file"]:
                    no_path.append("food_nutrient.csv")

                # Tell the user which paths are missing
                raise CommandError(
                    f"Path{'s' if len(no_path) > 1 else ''} to {', '.join(no_path)}"
                    f" {'were' if len(no_path) > 1 else 'was'} not provided."
                )
        else:
            # Search for files with the names as available on the FDC
            # website and override if a specific path was provided.
            food_file = Path(options["food_file"] or data_dir / "food.csv")
            nutrient_file = Path(options["nutrient_file"] or data_dir / "nutrient.csv")
            food_nutrient_file = Path(
                options["food_nutrient_file"] or data_dir / "food_nutrient.csv"
            )

        # Check if files can be located
        missing_files = []
        for file in food_file, nutrient_file, food_nutrient_file:
            if not file.exists():
                missing_files.append(file.name)
        if missing_files:
            raise CommandError(
                f"File(s) {', '.join(missing_files)} could not be located."
            )

        # Create Ingredients
        create_fdc_data_source()
        ingredients = models.Ingredient.objects.bulk_create(
            parse_food_csv(food_file, options["dataset_filter"]), ignore_conflicts=True
        )

        # Create IngredientNutrients
        try:
            parse_food_nutrient_csv(food_nutrient_file, nutrient_file)
        except NoNutrientException:
            raise CommandError(
                "Required nutrients not found in the database. You can add these "
                "nutrients by calling the 'populatenutrientdata' command."
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully added {len(ingredients)} ingredients.")
        )


def create_fdc_data_source() -> models.FoodDataSource:
    """Create a FoodDataSource record for USDA's Food Data Central."""
    return models.FoodDataSource.objects.get_or_create(name="FDC")


def get_nutrient_units(file: Union[str, os.PathLike, io.IOBase]) -> Dict[int, str]:
    """Retrieve nutrient units from the FDC nutrient.csv file.

    Parameters
    ----------
    file
        File or path to the file containing nutrient data.
    """
    result = {}
    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for nutrient_record in reader:

            # Ignore nutrients that are not needed for the functioning
            # of the app and convert non-standard units to their
            # respective standard nutrients.
            unit = nutrient_record.get("unit_name")

            # Map nutrient's FDC id to it's unit
            result[int(nutrient_record.get("id"))] = UNIT_CONVERSION.get(unit) or unit

    return result


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
        'branded_food', 'experimental_food', 'sr_legacy_food',
        'sample_food', 'market_acquistion', 'sub_sample_food',
        'foundation_food', 'agricultural_acquisition',
        'survey_fndds_food'
    """
    data_source = models.FoodDataSource.objects.get(name="FDC")
    ingredient_list = []
    # If no dataset_filter was provided use FDC_DATA_SOURCES that
    # contains all FDC datasets
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
) -> List[models.IngredientNutrient]:
    """Load per ingredient nutrient data from a food_nutrient.csv file.

    If either the ingredient or the nutrient of a record (row) is not
    in the database the record will be skipped.

    Parameters
    ----------
    file
        File or path to the file containing ingredient nutrient data.
    nutrient_file
        File or path to the containing nutrient data.
    """

    # Mapping of FDC nutrient ids to this app's nutrient instances.
    # nutrients = <nutrient_fdc_id> : <nutrient_instance>
    nutrients = models.Nutrient.objects.filter(name__in=FDC_TO_NUTRIENT.values())
    # No IngredientNutrients will be created if the nutrients are not
    # in the database.
    if not nutrients.exists():
        raise NoNutrientException("No nutrients found")

    nutrients = {n.name: n for n in nutrients}
    nutrients = {
        id_: nutrients[name]
        for id_, name in FDC_TO_NUTRIENT.items()
        if name in nutrients
    }

    # Mapping of FDC id of nutrients to their units in the FDC database.
    # units = <nutrient_fdc_id> : <nutrient_fdc_unit>
    # c_f = <nutrient_fdc_id> : <conversion_factor(fdc_unit -> app_unit)>
    units = get_nutrient_units(nutrient_file)
    conversion_factors = {}
    for id_, unit in units.items():
        nutrient = nutrients.get(id_)
        if nutrient is not None:
            factor = get_conversion_factor(unit, nutrient.unit, nutrient.name)
            conversion_factors[id_] = factor

    # Mappings used to convert FDC ids to ingredients.
    ingredients = models.Ingredient.objects.filter(data_source__name="FDC")
    ingredient_ids = {i.external_id: i for i in ingredients}

    # List of IngredientNutrient instances created from data in
    # food_nutrient.csv
    ingredient_nutrient_list = []

    # Data for IngredientNutrients where nutrients need to be treated
    # differently
    nonstandard = {}

    with open_or_pass(file, newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:

            # Get instances and final amount.
            ingredient = ingredient_ids.get(int(record.get("fdc_id")))
            nutrient_id = int(record.get("nutrient_id"))  # FDC nutrient id
            nutrient = nutrients.get(nutrient_id)

            # Skip if either ingredient or nutrient is not in DB.
            if ingredient is None or nutrient is None:
                continue

            # Grab amount and convert units if necessary
            amount = float(record["amount"]) * conversion_factors[nutrient_id]

            if nutrient_id in FDC_EXCEPTION_IDS:
                handle_nonstandard(
                    ingredient, nutrient, nutrient_id, nonstandard, amount
                )
                continue

            ingredient_nutrient = models.IngredientNutrient(
                ingredient=ingredient, nutrient=nutrient, amount=amount
            )
            ingredient_nutrient_list.append(ingredient_nutrient)

    for ingredient, nutrients in nonstandard.items():
        ing_nuts = [
            models.IngredientNutrient(
                ingredient=ingredient, nutrient=nutrient, amount=amount
            )
            for nutrient, amount in nutrients.items()
        ]
        ingredient_nutrient_list.extend(ing_nuts)

    return models.IngredientNutrient.objects.bulk_create(ingredient_nutrient_list)


def handle_nonstandard(ingredient, nutrient, fdc_id, output_dict, amount):
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
    elif fdc_id in PREFERRED_NON_STANDARD:
        output_dict[ingredient][nutrient] = amount

    # Vitamin K
    # Summed up because vitamin K appears as 3 different molecules.
    elif fdc_id in {1183, 1184, 1185}:
        output_dict[ingredient][nutrient] += amount


class NoNutrientException(Exception):
    """
    Raised when the nutrients required for a process are not present
    in the database.
    """
