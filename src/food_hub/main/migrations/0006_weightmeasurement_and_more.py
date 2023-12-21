"""Add the `WeightMeasurement` model."""

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_mealcomponent_to_recipe_repurpose_squashed"),
    ]

    operations = [
        migrations.CreateModel(
            name="WeightMeasurement",
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
                    "value",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                ("time", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weight_measurements",
                        to="main.profile",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="weightmeasurement",
            constraint=models.UniqueConstraint(
                models.F("profile"),
                models.F("time"),
                name="unique_main_weightmeasurement_profile_time",
            ),
        ),
    ]
