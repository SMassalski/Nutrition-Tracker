"""Add the `tracked_nutrients` field to the Profile model."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_weightmeasurement_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="tracked_nutrients",
            field=models.ManyToManyField(to="main.nutrient"),
        ),
    ]
