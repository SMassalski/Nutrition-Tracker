"""Creates meal associate models (Meal, MealComponent,
MealComponentAmount and MealComponentIngredient) and the Profile model.

Additionally, adds `IngredientNutrient.ingredient` related name.
"""
# Generated by Django 4.1.4 on 2023-04-25 11:39

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_ingredient_nutrient_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ingredientnutrient",
            name="ingredient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="nutrients",
                to="main.ingredient",
            ),
        ),
        migrations.CreateModel(
            name="Meal",
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
                ("date", models.DateTimeField()),
                ("name", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="MealComponent",
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
                ("name", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="MealComponentIngredient",
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
                ("amount", models.FloatField()),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.ingredient",
                    ),
                ),
                (
                    "meal_component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ingredients",
                        to="main.mealcomponent",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MealComponentAmount",
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
                ("amount", models.FloatField()),
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.mealcomponent",
                    ),
                ),
                (
                    "meal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="components",
                        to="main.meal",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="mealcomponentingredient",
            constraint=models.UniqueConstraint(
                models.F("meal_component"),
                models.F("ingredient"),
                name="unique_meal_component_ingredient",
            ),
        ),
        migrations.AddConstraint(
            model_name="mealcomponentamount",
            constraint=models.UniqueConstraint(
                models.F("meal"), models.F("component"), name="unique_meal_component"
            ),
        ),
        migrations.AddField(
            model_name="meal",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="meals",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="mealcomponent",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="meal_components",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="meal",
            name="date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="mealcomponent",
            name="final_weight",
            field=models.FloatField(),
        ),
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
                ("age", models.PositiveIntegerField()),
                (
                    "activity_level",
                    models.CharField(
                        choices=[
                            ("S", "Sedentary"),
                            ("LA", "Low Active"),
                            ("A", "Active"),
                            ("VA", "Very Active"),
                        ],
                        max_length=2,
                    ),
                ),
                ("height", models.PositiveIntegerField()),
                (
                    "sex",
                    models.CharField(
                        choices=[("M", "Male"), ("F", "Female")], max_length=1
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("energy_requirement", models.PositiveIntegerField()),
                ("weight", models.PositiveIntegerField()),
            ],
        ),
    ]