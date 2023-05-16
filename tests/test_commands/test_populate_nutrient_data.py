"""Tests of the populate_nutrient_data command."""
from django.core.management import call_command
from main.management.commands._data import FULL_NUTRIENT_DATA
from main.management.commands.populatenutrientdata import create_nutrients
from main.models import Nutrient

NAMES = [nut["name"] for nut in FULL_NUTRIENT_DATA]


def test_create_nutrients(db):
    """
    create_nutrients() saves to the database all specified nutrients.
    """

    create_nutrients()
    assert Nutrient.objects.filter(name__in=NAMES).count() == len(NAMES)


def test_create_nutrients_already_existing_nutrient(db):
    """
    create_nutrients() does not raise an exception if a nutrient that
    would be created by create_nutrients() already exists.
    """
    Nutrient.objects.create(name="Protein", unit="G")
    create_nutrients()


def test_populate_nutrient_data_command(db):
    """
    The populate_nutrient_data command saves to the database all
    specified nutrients.
    """
    call_command("populatenutrientdata")
    assert Nutrient.objects.filter(name__in=NAMES).count() == len(NAMES)
