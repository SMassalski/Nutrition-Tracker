# Generated by Django 4.1.3 on 2022-11-28 09:18

from django.conf import settings
from django.db import migrations
from util.parse_fdc_data import parse_nutrient_csv


def parse_nutrients(apps, schema_editor):
    """Load data from nutrient csv"""
    Nutrient = apps.get_model("main", "Nutrient")
    parse_nutrient_csv(Nutrient, settings.NUTRIENT_FILE)


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_alter_nutrient_unit"),
    ]

    operations = [migrations.RunPython(parse_nutrients)]
