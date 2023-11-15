"""
Command for populating the database with data from Food Data Central csv
files.
"""
from pathlib import Path
from typing import Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from main import models

from ._fdc_helpers import NoNutrientException, get_fdc_data_source
from ._fdc_parsers import FDC_DATASETS, parse_food_csv, parse_food_nutrient_csv

DATA_DIR = getattr(settings, "DATA_DIR", None)

# FDC IDs of the preferred FDC nutrient counterparts (if one exists)
PREFERRED_NONSTANDARD = {
    1232,  # Cysteine
    1106,  # Vitamin A, RAE
    1114,  # Vitamin D (D2 + D3)
    1177,  # Folate, total
}
VITAMIN_K_IDS = {1183, 1184, 1185}


class Command(BaseCommand):
    """Populate the database with data from FDC csv files."""

    help = (
        "Populates the database with data from Food Data Central csv files. "
        "By default the command looks for the files in the directory indicated by "
        "the DATA_DIR setting."
    )

    def __init__(self, preferred=None, additive=None, **kwargs):
        """Command for populating the database with data from FDC csv.

        Parameters
        ----------
        preferred: collections.abc.Container
            The FDC ids that should take priority if the referred to
            nutrient has multiple entries in the FDC database.
        additive: collections.abc.Container
            The FDC ids that should be summed together if the referred
            to nutrient has multiple entries in the FDC database.
        kwargs
        """
        super().__init__(**kwargs)
        self.preferred = PREFERRED_NONSTANDARD if preferred is None else preferred
        self.additive = VITAMIN_K_IDS if additive is None else additive

    # docstr-coverage: inherited
    def add_arguments(self, parser):
        parser.add_argument(
            "--data_dir",
            type=str,
            help="Directory where the data files are located.",
            default=DATA_DIR,
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
            choices=FDC_DATASETS,
            help="If provided only saves food records from specified FDC datasets. ",
            default=FDC_DATASETS,
        )

        parser.add_argument(
            "--batch_size",
            type=int,
            help="The max number of IngredientNutrient records to save per batch."
            "If not set saves all records in a single batch. Helps with memory"
            "limitations.",
        )

    # docstr-coverage: inherited
    def handle(self, *args, **options):

        food_file, nutrient_file, food_nutrient_file = _select_files(options)

        data_source = get_fdc_data_source()
        ing_count = len(
            models.Ingredient.objects.bulk_create(
                parse_food_csv(food_file, options["dataset_filter"], data_source),
                ignore_conflicts=True,
            )
        )
        self.stdout.write(self.style.SUCCESS("Ingredients saved."))

        # Create IngredientNutrients
        try:
            parse_food_nutrient_csv(
                food_nutrient_file,
                nutrient_file,
                options["batch_size"],
                preferred_nutrients=self.preferred,
                additive_nutrients=self.additive,
            )
        except NoNutrientException:
            raise CommandError(
                "Required nutrients not found in the database. You can add these "
                "nutrients by calling the 'loadnutrientdata' command."
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully added {ing_count} ingredients.")
        )


def _select_files(options) -> Tuple[Path, Path, Path]:
    """Select the correct FDC file paths from the loadfdcdata arguments.

    Parameters
    ----------
    options
        The keyword arguments to the loadfdcdata command's handle
        method.

    Returns
    -------
    Tuple[Path, Path, Path]
        The FoodDataCentral food.csv, nutrient.csv and food_nutrient.csv
        files in that order.
    """
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
        raise CommandError(f"File(s) {', '.join(missing_files)} could not be located.")

    return food_file, nutrient_file, food_nutrient_file
