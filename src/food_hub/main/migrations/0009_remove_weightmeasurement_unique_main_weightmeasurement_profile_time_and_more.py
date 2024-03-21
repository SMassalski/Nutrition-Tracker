"""Modify WeightMeasurement model.

time: Change to DateField
value: Change to FloatField with min value of 0.1
Remove time & profile unique together constraint.
"""
import datetime

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_alter_profile_tracked_nutrients"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="weightmeasurement",
            name="unique_main_weightmeasurement_profile_time",
        ),
        migrations.RemoveField(
            model_name="weightmeasurement",
            name="time",
        ),
        migrations.AddField(
            model_name="weightmeasurement",
            name="date",
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name="weightmeasurement",
            name="value",
            field=models.FloatField(
                validators=[django.core.validators.MinValueValidator(0.1)]
            ),
        ),
    ]
