"""
Set blank to `True` for nullable fields in the Nutrient and
IntakeRecommendation models.
"""

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_nutrient_energy_delete_nutrientenergy"),
    ]

    operations = [
        migrations.AlterField(
            model_name="intakerecommendation",
            name="age_max",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="intakerecommendation",
            name="amount_max",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="intakerecommendation",
            name="amount_min",
            field=models.FloatField(
                blank=True,
                help_text="Use of the amount fields differs depending on the selected <em>dri_type</em>.</br>* AMDR - <em>amount_min</em> and <em>amount_max</em> are the lower and the upper limits of the range respectively.</br>* AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - <em>amount_min</em> is the RDA or AI value. <em>amount_max</em> is the UL value (if available).</br>* AIK - use only <em>amount_min</em>.</br>* UL - uses only <em>amount_max</em>.</br>* ALAP - ignores both.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="nutrient",
            name="types",
            field=models.ManyToManyField(
                blank=True, related_name="nutrients", to="main.nutrienttype"
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="tracked_nutrients",
            field=models.ManyToManyField(
                blank=True, related_name="tracking_profiles", to="main.nutrient"
            ),
        ),
    ]
