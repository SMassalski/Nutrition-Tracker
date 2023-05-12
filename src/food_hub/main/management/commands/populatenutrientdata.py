"""Command and associated functions for populating nutrient data."""
from django.core.management.base import BaseCommand
from main.models import Nutrient


class Command(BaseCommand):
    """
    Command populating the database with nutrient data required for the
    functioning of the application.
    """

    help = "Populates the database with nutrient data."

    # docstr-coverage: inherited
    def handle(self, *args, **options):
        create_nutrients()


def create_nutrients():
    """Create and save nutrient entries for important nutrients."""
    nutrient_data = [
        {"name": "Protein", "unit": "G"},
        {"name": "Lipid", "unit": "G"},
        {"name": "Carbohydrate", "unit": "G"},
        {"name": "Ash", "unit": "G"},
        {"name": "Fiber", "unit": "G"},
        {"name": "Energy", "unit": "KCAL"},
        {"name": "Water", "unit": "G"},
        {"name": "Arsenic", "unit": "UG"},
        {"name": "Boron", "unit": "MG"},
        {"name": "Calcium", "unit": "MG"},
        {"name": "Chlorine", "unit": "G"},
        {"name": "Chromium", "unit": "UG"},
        {"name": "Copper", "unit": "UG"},
        {"name": "Fluoride", "unit": "MG"},
        {"name": "Iodine", "unit": "UG"},
        {"name": "Iron", "unit": "MG"},
        {"name": "Magnesium", "unit": "MG"},
        {"name": "Manganese", "unit": "MG"},
        {"name": "Molybdenum", "unit": "UG"},
        {"name": "Nickel", "unit": "MG"},
        {"name": "Phosphorus", "unit": "MG"},
        {"name": "Potassium", "unit": "G"},
        {"name": "Selenium", "unit": "UG"},
        {"name": "Silicon", "unit": "UG"},
        {"name": "Sodium", "unit": "G"},
        {"name": "Vanadium", "unit": "MG"},
        {"name": "Zinc", "unit": "MG"},
        {"name": "Vitamin B1", "unit": "MG"},
        {"name": "Vitamin B2", "unit": "MG"},
        {"name": "Vitamin B3", "unit": "MG"},
        {"name": "Vitamin B5", "unit": "MG"},
        {"name": "Vitamin B6", "unit": "MG"},
        {"name": "Vitamin B7", "unit": "UG"},
        {"name": "Vitamin B9", "unit": "UG"},
        {"name": "Vitamin B12", "unit": "UG"},
        {"name": "Vitamin A", "unit": "UG"},
        {"name": "Vitamin C", "unit": "MG"},
        {"name": "Vitamin D", "unit": "UG"},
        {"name": "Vitamin D2", "unit": "UG"},
        {"name": "Vitamin D3", "unit": "UG"},
        {"name": "Vitamin E", "unit": "MG"},
        {"name": "Vitamin K", "unit": "UG"},
        {"name": "Alanine", "unit": "MG"},
        {"name": "Arginine", "unit": "MG"},
        {"name": "Aspartic acid", "unit": "MG"},
        {"name": "Asparagine", "unit": "MG"},
        {"name": "Cysteine", "unit": "MG"},
        {"name": "Glutamic acid", "unit": "MG"},
        {"name": "Glutamine", "unit": "MG"},
        {"name": "Glycine", "unit": "MG"},
        {"name": "Histidine", "unit": "MG"},
        {"name": "Isoleucine", "unit": "MG"},
        {"name": "Leucine", "unit": "MG"},
        {"name": "Lysine", "unit": "MG"},
        {"name": "Methionine", "unit": "MG"},
        {"name": "Phenylalanine", "unit": "MG"},
        {"name": "Proline", "unit": "MG"},
        {"name": "Serine", "unit": "MG"},
        {"name": "Threonine", "unit": "MG"},
        {"name": "Tryptophan", "unit": "MG"},
        {"name": "Tyrosine", "unit": "MG"},
        {"name": "Valine", "unit": "MG"},
        {"name": "Saturated fatty acids", "unit": "G"},
        {"name": "Monounsaturated fatty acids", "unit": "G"},
        {"name": "Polyunsaturated fatty acids", "unit": "G"},
        {"name": "Trans fatty acids", "unit": "G"},
        {"name": "Cholesterol", "unit": "MG"},
        {"name": "Sugars", "unit": "G"},
        {"name": "Sugars (added)", "unit": "G"},
        {"name": "alpha-Linolenic acid", "unit": "G"},
        {"name": "Linoleic acid", "unit": "G"},
        {"name": "Choline", "unit": "MG"},
    ]
    instances = [Nutrient(**data) for data in nutrient_data]
    Nutrient.objects.bulk_create(instances, ignore_conflicts=True)


class NoNutrientException(Exception):
    """
    Raised when the nutrients required for a process are not present
    in the database.
    """
