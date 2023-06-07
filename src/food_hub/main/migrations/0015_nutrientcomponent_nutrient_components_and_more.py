# Generated by Django 4.1.4 on 2023-06-07 08:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0014_nutrienttype_displayed_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="NutrientComponent",
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
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="main.nutrient"
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="component_nutrient_components",
                        to="main.nutrient",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="nutrient",
            name="components",
            field=models.ManyToManyField(
                related_name="compounds",
                through="main.NutrientComponent",
                to="main.nutrient",
            ),
        ),
        migrations.AddConstraint(
            model_name="nutrientcomponent",
            constraint=models.CheckConstraint(
                check=models.Q(("component", models.F("target")), _negated=True),
                name="main_nutrientcomponent_compound_nutrient_cant_be_component",
            ),
        ),
        migrations.AddConstraint(
            model_name="nutrientcomponent",
            constraint=models.UniqueConstraint(
                fields=("target", "component"), name="main_nutrientcomponent_unique"
            ),
        ),
    ]