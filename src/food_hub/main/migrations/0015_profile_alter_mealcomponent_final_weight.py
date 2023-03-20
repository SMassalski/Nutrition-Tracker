# Generated by Django 4.1.4 on 2023-03-10 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "main",
            "0010_meal_mealcomponent_mealcomponentingredient_and_more_squashed_0014_rename_final_mass_mealcomponent_final_weight",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
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
                ("age", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "activity_level",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("S", "Sedentary"),
                            ("LA", "Low Active"),
                            ("A", "Active"),
                            ("VA", "Very Active"),
                        ],
                        max_length=2,
                    ),
                ),
                ("height", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "sex",
                    models.CharField(
                        blank=True,
                        choices=[("M", "Male"), ("F", "Female")],
                        max_length=1,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="mealcomponent",
            name="final_weight",
            field=models.FloatField(),
        ),
    ]
