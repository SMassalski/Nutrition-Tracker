"""
Change the IngredientNutrient model's amount field from an integer field
ta a float field.
"""
# Generated by Django 4.1.3 on 2022-11-30 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_ingredientnutrient_unique_ingredient_nutrient"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ingredientnutrient",
            name="amount",
            field=models.FloatField(),
        ),
    ]