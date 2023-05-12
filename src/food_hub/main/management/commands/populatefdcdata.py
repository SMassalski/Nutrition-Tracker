"""
Command for populating the database with data from Food Data Central csv
files.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from main import models

from ._populatefdcdata import (
    create_fdc_data_source,
    parse_food_csv,
    parse_food_nutrient_csv,
)
from .populatenutrientdata import NoNutrientException


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
            "Available datasets: 'sr_legacy_food', 'survey_fndds_food'",
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

        # CONFIG CHECKS

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

        # READING AND SAVING THE DATA

        # Create Ingredients
        create_fdc_data_source()
        ing_count = len(
            models.Ingredient.objects.bulk_create(
                parse_food_csv(food_file, options["dataset_filter"]),
                ignore_conflicts=True,
            )
        )
        self.stdout.write(self.style.SUCCESS("Ingredients saved."))

        # Create IngredientNutrients
        try:
            parse_food_nutrient_csv(
                food_nutrient_file, nutrient_file, options["batch_size"]
            )
        except NoNutrientException:
            raise CommandError(
                "Required nutrients not found in the database. You can add these "
                "nutrients by calling the 'populatenutrientdata' command."
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully added {ing_count} ingredients.")
        )
