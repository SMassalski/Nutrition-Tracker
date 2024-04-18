"""Change the Meal.date default function."""

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0012_alter_ingredient_data_source_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="meal",
            name="date",
            field=models.DateField(default=datetime.date.today),
        ),
    ]
