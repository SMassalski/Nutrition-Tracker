"""Replace the `NutrientEnergy` model with a field."""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "main",
            "0009_remove_weightmeasurement_unique_main_weightmeasurement_profile_time_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="nutrient",
            name="energy",
            field=models.FloatField(
                default=0, validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
        migrations.DeleteModel(
            name="NutrientEnergy",
        ),
    ]
