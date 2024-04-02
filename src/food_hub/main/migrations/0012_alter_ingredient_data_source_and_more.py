"""
Set blank to `True` for nullable fields in the Ingredient and
Recipe models.
"""

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0011_alter_ingredient_data_source_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ingredient",
            name="data_source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="main.fooddatasource",
            ),
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="dataset",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="external_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="final_weight",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.1)],
            ),
        ),
    ]
