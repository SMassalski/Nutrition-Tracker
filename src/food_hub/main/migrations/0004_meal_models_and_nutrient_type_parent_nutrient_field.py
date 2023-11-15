"""
Modifies the `Meal` model and its constraints, and added a
MealIngredient model. Adds the `parent_nutrient` field to the
NutrientType model.
"""

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0003_recommendation_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="MealIngredient",
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
            ],
        ),
        migrations.RemoveField(
            model_name="meal",
            name="name",
        ),
        migrations.RemoveField(
            model_name="meal",
            name="user",
        ),
        migrations.AddField(
            model_name="meal",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="main.profile",
            ),
        ),
        migrations.AlterField(
            model_name="meal",
            name="date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddConstraint(
            model_name="meal",
            constraint=models.UniqueConstraint(
                models.F("owner"), models.F("date"), name="meal_unique_profile_date"
            ),
        ),
        migrations.AddField(
            model_name="mealingredient",
            name="ingredient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="main.ingredient"
            ),
        ),
        migrations.AddField(
            model_name="mealingredient",
            name="meal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="main.meal"
            ),
        ),
        migrations.AddField(
            model_name="meal",
            name="ingredients",
            field=models.ManyToManyField(
                through="main.MealIngredient", to="main.ingredient"
            ),
        ),
        migrations.AddConstraint(
            model_name="mealingredient",
            constraint=models.UniqueConstraint(
                models.F("ingredient"), models.F("meal"), name="unique_meal_ingredient"
            ),
        ),
        migrations.AlterField(
            model_name="meal",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="main.profile"
            ),
        ),
        migrations.RemoveConstraint(
            model_name="mealingredient",
            name="unique_meal_ingredient",
        ),
        migrations.AlterField(
            model_name="mealingredient",
            name="amount",
            field=models.FloatField(
                validators=[django.core.validators.MinValueValidator(0.1)]
            ),
        ),
        migrations.AddField(
            model_name="nutrienttype",
            name="parent_nutrient",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="child_type",
                to="main.nutrient",
            ),
        ),
    ]
