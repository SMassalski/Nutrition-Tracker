# Generated by Django 4.1.3 on 2022-12-06 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0013_mealcomponent_final_mass"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mealcomponent",
            old_name="final_mass",
            new_name="final_weight",
        ),
    ]
