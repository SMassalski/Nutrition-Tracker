"""Repurpose of the MealComponent models for the Recipe system."""


import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_meal_models_and_nutrient_type_parent_nutrient_field"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="MealComponent",
            new_name="Recipe",
        ),
        migrations.RemoveField(
            model_name="recipe",
            name="user",
        ),
        migrations.AddField(
            model_name="recipe",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recipes",
                to="main.profile",
            ),
        ),
        migrations.RenameModel(
            old_name="MealComponentIngredient",
            new_name="RecipeIngredient",
        ),
        migrations.RemoveConstraint(
            model_name="recipeingredient",
            name="unique_meal_component_ingredient",
        ),
        migrations.RemoveField(
            model_name="recipeingredient",
            name="meal_component",
        ),
        migrations.AddField(
            model_name="recipe",
            name="ingredients",
            field=models.ManyToManyField(
                through="main.RecipeIngredient", to="main.ingredient"
            ),
        ),
        migrations.AddField(
            model_name="recipeingredient",
            name="recipe",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="main.recipe"
            ),
        ),
        migrations.AddConstraint(
            model_name="recipeingredient",
            constraint=models.UniqueConstraint(
                models.F("recipe"),
                models.F("ingredient"),
                name="unique_recipe_ingredient",
            ),
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="main.recipe"
            ),
        ),
        migrations.RenameModel(
            old_name="MealComponentAmount",
            new_name="RecipeAmount",
        ),
        migrations.RemoveConstraint(
            model_name="recipeamount",
            name="unique_meal_component",
        ),
        migrations.RenameField(
            model_name="recipeamount",
            old_name="component",
            new_name="recipe",
        ),
        migrations.AddField(
            model_name="meal",
            name="recipes",
            field=models.ManyToManyField(through="main.RecipeAmount", to="main.recipe"),
        ),
        migrations.AlterField(
            model_name="recipeamount",
            name="meal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="main.meal"
            ),
        ),
        migrations.AddConstraint(
            model_name="recipeamount",
            constraint=models.UniqueConstraint(
                models.F("meal"), models.F("recipe"), name="unique_meal_component"
            ),
        ),
        migrations.RemoveConstraint(
            model_name="recipeamount",
            name="unique_meal_component",
        ),
        migrations.RenameModel(
            old_name="RecipeAmount",
            new_name="MealRecipe",
        ),
        migrations.RemoveConstraint(
            model_name="recipeingredient",
            name="unique_recipe_ingredient",
        ),
        migrations.AddField(
            model_name="recipe",
            name="slug",
            field=models.SlugField(null=True),
        ),
        migrations.AlterField(
            model_name="mealrecipe",
            name="amount",
            field=models.FloatField(
                validators=[django.core.validators.MinValueValidator(0.1)]
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="final_weight",
            field=models.FloatField(
                validators=[django.core.validators.MinValueValidator(0.1)]
            ),
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="amount",
            field=models.FloatField(
                validators=[django.core.validators.MinValueValidator(0.1)]
            ),
        ),
        migrations.AddConstraint(
            model_name="recipe",
            constraint=models.UniqueConstraint(
                models.F("owner"), models.F("slug"), name="recipe_unique_owner_slug"
            ),
        ),
        migrations.AddConstraint(
            model_name="recipe",
            constraint=models.UniqueConstraint(
                models.F("owner"), models.F("name"), name="recipe_unique_owner_name"
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="final_weight",
            field=models.FloatField(
                null=True, validators=[django.core.validators.MinValueValidator(0.1)]
            ),
        ),
    ]
