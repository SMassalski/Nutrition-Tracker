"""
Adds a unique together constraint to IngredientNutrients' ingredient
and nutrient fields, and changes the amount field to a float field.
"""
# Generated by Django 4.1.4 on 2023-04-25 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_ingredient_data"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="ingredientnutrient",
            constraint=models.UniqueConstraint(
                models.F("ingredient"),
                models.F("nutrient"),
                name="unique_ingredient_nutrient",
            ),
        ),
        migrations.AlterField(
            model_name="ingredientnutrient",
            name="amount",
            field=models.FloatField(),
        ),
    ]
