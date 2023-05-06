"""Creates intermediate nutrient and ingredient nutrient tables.

Additionally, adds unique constraint to `FoodDataSource.name`.
"""
# Generated by Django 4.1.4 on 2023-04-25 11:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0021_ingredient_and_nutrient_fdc_datasource_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fooddatasource",
            name="name",
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.CreateModel(
            name="IntermediateNutrient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name="nutrient",
            name="internal_nutrient",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="main.intermediatenutrient",
            ),
        ),
        migrations.CreateModel(
            name="IntermediateIngredientNutrient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.FloatField()),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.ingredient",
                    ),
                ),
                (
                    "nutrient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.intermediatenutrient",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="ingredient",
            name="intermediate_nutrients",
            field=models.ManyToManyField(
                through="main.IntermediateIngredientNutrient",
                to="main.intermediatenutrient",
            ),
        ),
        migrations.AddConstraint(
            model_name="intermediateingredientnutrient",
            constraint=models.UniqueConstraint(
                models.F("ingredient"),
                models.F("nutrient"),
                name="unique_ingredient_intermediate_nutrient",
            ),
        ),
        migrations.AddField(
            model_name="intermediatenutrient",
            name="unit",
            field=models.CharField(
                choices=[
                    ("KCAL", "calories"),
                    ("G", "grams"),
                    ("MG", "milligrams"),
                    ("UG", "micrograms"),
                    ("IU", "IU"),
                ],
                default="UG",
                max_length=10,
            ),
            preserve_default=False,
        ),
    ]