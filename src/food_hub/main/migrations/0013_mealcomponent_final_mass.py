# Generated by Django 4.1.3 on 2022-12-06 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0012_alter_meal_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="mealcomponent",
            name="final_mass",
            field=models.FloatField(default=100),
            preserve_default=False,
        ),
    ]
