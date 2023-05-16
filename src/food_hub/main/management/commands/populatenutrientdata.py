"""Command and associated functions for populating nutrient data."""
from django.core.management.base import BaseCommand
from main.models import Nutrient

from ._data import FULL_NUTRIENT_DATA


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
        {"name": nut["name"], "unit": nut["unit"]} for nut in FULL_NUTRIENT_DATA
    ]
    instances = [Nutrient(**data) for data in nutrient_data]
    Nutrient.objects.bulk_create(instances, ignore_conflicts=True)
