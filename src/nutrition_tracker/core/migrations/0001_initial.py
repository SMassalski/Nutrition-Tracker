"""Create models and constraints for the core app."""

import datetime

import django.core.validators
import django.db.models.lookups
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FoodDataSource",
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
                ("name", models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Ingredient",
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
                ("external_id", models.IntegerField(blank=True, null=True)),
                ("name", models.CharField(max_length=200)),
                ("dataset", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "data_source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.fooddatasource",
                    ),
                ),
            ],
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
                ("date", models.DateField(default=datetime.date.today)),
            ],
        ),
        migrations.CreateModel(
            name="Nutrient",
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
                ("name", models.CharField(max_length=32, unique=True)),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("KCAL", "calories"),
                            ("G", "grams"),
                            ("MG", "milligrams"),
                            ("UG", "micrograms"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "energy",
                    models.FloatField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
            ],
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
                ("height", models.PositiveIntegerField()),
                ("weight", models.PositiveIntegerField()),
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
                (
                    "sex",
                    models.CharField(
                        choices=[("M", "Male"), ("F", "Female")], max_length=1
                    ),
                ),
                ("energy_requirement", models.PositiveIntegerField()),
                (
                    "tracked_nutrients",
                    models.ManyToManyField(
                        blank=True, related_name="tracking_profiles", to="core.nutrient"
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Recipe",
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
                (
                    "final_weight",
                    models.FloatField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(0.1)],
                    ),
                ),
                ("slug", models.SlugField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="WeightMeasurement",
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
                (
                    "value",
                    models.FloatField(
                        validators=[django.core.validators.MinValueValidator(0.1)]
                    ),
                ),
                ("date", models.DateField(default=datetime.date.today)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weight_measurements",
                        to="core.profile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RecipeIngredient",
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
                (
                    "amount",
                    models.FloatField(
                        validators=[django.core.validators.MinValueValidator(0.1)]
                    ),
                ),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.ingredient",
                    ),
                ),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.recipe"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="recipe",
            name="ingredients",
            field=models.ManyToManyField(
                through="core.RecipeIngredient", to="core.ingredient"
            ),
        ),
        migrations.AddField(
            model_name="recipe",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recipes",
                to="core.profile",
            ),
        ),
        migrations.CreateModel(
            name="NutrientType",
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
                ("name", models.CharField(max_length=32, unique=True)),
                ("displayed_name", models.CharField(max_length=32, null=True)),
                (
                    "parent_nutrient",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="child_type",
                        to="core.nutrient",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NutrientComponent",
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
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.nutrient"
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="component_nutrient_components",
                        to="core.nutrient",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="nutrient",
            name="components",
            field=models.ManyToManyField(
                related_name="compounds",
                through="core.NutrientComponent",
                to="core.nutrient",
            ),
        ),
        migrations.AddField(
            model_name="nutrient",
            name="types",
            field=models.ManyToManyField(
                blank=True, related_name="nutrients", to="core.nutrienttype"
            ),
        ),
        migrations.CreateModel(
            name="MealRecipe",
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
                (
                    "amount",
                    models.FloatField(
                        validators=[django.core.validators.MinValueValidator(0.1)]
                    ),
                ),
                (
                    "meal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.meal"
                    ),
                ),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.recipe"
                    ),
                ),
            ],
        ),
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
                (
                    "amount",
                    models.FloatField(
                        validators=[django.core.validators.MinValueValidator(0.1)]
                    ),
                ),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.ingredient",
                    ),
                ),
                (
                    "meal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.meal"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="meal",
            name="ingredients",
            field=models.ManyToManyField(
                through="core.MealIngredient", to="core.ingredient"
            ),
        ),
        migrations.AddField(
            model_name="meal",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="core.profile"
            ),
        ),
        migrations.AddField(
            model_name="meal",
            name="recipes",
            field=models.ManyToManyField(through="core.MealRecipe", to="core.recipe"),
        ),
        migrations.CreateModel(
            name="IntakeRecommendation",
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
                (
                    "dri_type",
                    models.CharField(
                        choices=[
                            ("AI", "AI/UL"),
                            ("AIK", "AI-KCAL"),
                            ("AI/KG", "AI/KG"),
                            ("ALAP", "As Low As Possible"),
                            ("AMDR", "AMDR"),
                            ("RDA", "RDA/UL"),
                            ("RDA/KG", "RDA/KG"),
                            ("UL", "UL"),
                        ],
                        max_length=6,
                    ),
                ),
                (
                    "sex",
                    models.CharField(
                        choices=[("B", "Both"), ("F", "Female"), ("M", "Male")],
                        max_length=1,
                    ),
                ),
                ("age_min", models.PositiveIntegerField()),
                ("age_max", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "amount_min",
                    models.FloatField(
                        blank=True,
                        help_text="Use of the amount fields differs depending on the selected <em>dri_type</em>.</br>* AMDR - <em>amount_min</em> and <em>amount_max</em> are the lower and the upper limits of the range respectively.</br>* AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - <em>amount_min</em> is the RDA or AI value. <em>amount_max</em> is the UL value (if available).</br>* AIK - use only <em>amount_min</em>.</br>* UL - uses only <em>amount_max</em>.</br>* ALAP - ignores both.",
                        null=True,
                    ),
                ),
                ("amount_max", models.FloatField(blank=True, null=True)),
                (
                    "nutrient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommendations",
                        to="core.nutrient",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IngredientNutrient",
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
                        to="core.ingredient",
                    ),
                ),
                (
                    "nutrient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.nutrient"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="ingredient",
            name="nutrients",
            field=models.ManyToManyField(
                through="core.IngredientNutrient", to="core.nutrient"
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
        migrations.AddConstraint(
            model_name="nutrientcomponent",
            constraint=models.CheckConstraint(
                check=models.Q(("component", models.F("target")), _negated=True),
                name="core_nutrientcomponent_compound_nutrient_cant_be_component",
            ),
        ),
        migrations.AddConstraint(
            model_name="nutrientcomponent",
            constraint=models.UniqueConstraint(
                fields=("target", "component"), name="core_nutrientcomponent_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="meal",
            constraint=models.UniqueConstraint(
                models.F("owner"), models.F("date"), name="meal_unique_profile_date"
            ),
        ),
        migrations.AddConstraint(
            model_name="intakerecommendation",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.LessThanOrEqual(
                    models.F("age_min"), models.F("age_max")
                ),
                name="recommendation_age_min_max",
            ),
        ),
        migrations.AddConstraint(
            model_name="intakerecommendation",
            constraint=models.CheckConstraint(
                check=django.db.models.lookups.LessThanOrEqual(
                    models.F("amount_min"), models.F("amount_max")
                ),
                name="recommendation_amount_min_max",
            ),
        ),
        migrations.AddConstraint(
            model_name="intakerecommendation",
            constraint=models.UniqueConstraint(
                fields=("sex", "age_min", "age_max", "dri_type", "nutrient"),
                name="recommendation_unique_demographic_nutrient_and_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="intakerecommendation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("age_max__isnull", True)),
                fields=("sex", "age_min", "dri_type", "nutrient"),
                name="recommendation_unique_demographic_nutrient_and_type_max_age_null",
            ),
        ),
        migrations.AddConstraint(
            model_name="ingredientnutrient",
            constraint=models.UniqueConstraint(
                models.F("ingredient"),
                models.F("nutrient"),
                name="unique_ingredient_nutrient",
            ),
        ),
        migrations.AddConstraint(
            model_name="ingredient",
            constraint=models.UniqueConstraint(
                fields=("data_source", "external_id"),
                name="unique_ingredient_data_source_and_external_id",
            ),
        ),
    ]
