"""Tests of the populate_nutrient_data command."""
from django.core.management import call_command
from main.management.commands.populatenutrientdata import create_nutrients
from main.models import Nutrient


def test_create_nutrients(db):
    """
    create_nutrients() saves to the database all specified nutrients.
    """
    names = [
        "Asparagine",
        "Phosphorus",
        "Vitamin D3",
        "Vitamin C",
        "Vitamin D",
        "Saturated fatty acids",
        "Chromium",
        "Threonine",
        "Vanadium",
        "Tryptophan",
        "Arsenic",
        "Cysteine",
        "Trans fatty acid",
        "Monounsaturated fatty acids",
        "Iodine",
        "Lysine",
        "Ash",
        "Polyunsaturated fatty acids",
        "Vitamin K",
        "Alanine",
        "Potassium",
        "Sodium",
        "Iron",
        "Vitamin B2",
        "Vitamin B6",
        "Aspartic acid",
        "Glutamine",
        "Serine",
        "Isoleucine",
        "Vitamin A",
        "Cholesterol",
        "Vitamin D2",
        "Protein",
        "Vitamin B5",
        "Manganese",
        "Fiber",
        "Fluoride",
        "Chlorine",
        "Glycine",
        "Glutamic acid",
        "Magnesium",
        "Silicon",
        "Zinc",
        "Vitamin B12",
        "Energy",
        "Nickel",
        "Lipid",
        "Sugars",
        "Leucine",
        "Phenylalanine",
        "Vitamin B9",
        "Calcium",
        "Carbohydrate",
        "Methionine",
        "Proline",
        "Histidine",
        "Selenium",
        "Vitamin B1",
        "Tyrosine",
        "Water",
        "Molybdenum",
        "Arginine",
        "Valine",
        "Vitamin B3",
        "Vitamin E",
        "Boron",
    ]
    create_nutrients()
    assert Nutrient.objects.filter(name__in=names).count() == 66


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
    names = [
        "Asparagine",
        "Phosphorus",
        "Vitamin D3",
        "Vitamin C",
        "Vitamin D",
        "Saturated fatty acids",
        "Chromium",
        "Threonine",
        "Vanadium",
        "Tryptophan",
        "Arsenic",
        "Cysteine",
        "Trans fatty acid",
        "Monounsaturated fatty acids",
        "Iodine",
        "Lysine",
        "Ash",
        "Polyunsaturated fatty acids",
        "Vitamin K",
        "Alanine",
        "Potassium",
        "Sodium",
        "Iron",
        "Vitamin B2",
        "Vitamin B6",
        "Aspartic acid",
        "Glutamine",
        "Serine",
        "Isoleucine",
        "Vitamin A",
        "Cholesterol",
        "Vitamin D2",
        "Protein",
        "Vitamin B5",
        "Manganese",
        "Fiber",
        "Fluoride",
        "Chlorine",
        "Glycine",
        "Glutamic acid",
        "Magnesium",
        "Silicon",
        "Zinc",
        "Vitamin B12",
        "Energy",
        "Nickel",
        "Lipid",
        "Sugars",
        "Leucine",
        "Phenylalanine",
        "Vitamin B9",
        "Calcium",
        "Carbohydrate",
        "Methionine",
        "Proline",
        "Histidine",
        "Selenium",
        "Vitamin B1",
        "Tyrosine",
        "Water",
        "Molybdenum",
        "Arginine",
        "Valine",
        "Vitamin B3",
        "Vitamin E",
        "Boron",
    ]
    call_command("populatenutrientdata")
    assert Nutrient.objects.filter(name__in=names).count() == 66
