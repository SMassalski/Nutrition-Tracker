"""Migration creating models related to recommendation features."""

import django.db.models.lookups
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("main", "0003_intakerecommendation"),
        ("main", "0004_alter_intakerecommendation_amount_min_and_more"),
        ("main", "0005_alter_intakerecommendation_dri_type"),
        ("main", "0006_alter_intakerecommendation_nutrient"),
        (
            "main",
            "0007_intakerecommendation_recommendation_unique_demographic_and_type",
        ),
        (
            "main",
            "0008_remove_intakerecommendation_recommendation_unique_demographic_and_type_and_more",
        ),
        ("main", "0009_nutrienttype_nutrient_type"),
        ("main", "0010_rename_type_nutrient_types"),
        ("main", "0011_nutrientenergy"),
        ("main", "0012_alter_nutrientenergy_options_and_more"),
        (
            "main",
            "0013_intakerecommendation_recommendation_unique_demographic_nutrient_and_type_max_age_null",
        ),
        ("main", "0014_nutrienttype_displayed_name"),
        ("main", "0015_nutrientcomponent_nutrient_components_and_more"),
        ("main", "0016_alter_intakerecommendation_amount_min"),
        ("main", "0017_alter_intakerecommendation_nutrient"),
    ]

    dependencies = [
        ("main", "0002_remove_ingredientnutrient_unique_ingredient_nutrient_and_more"),
    ]

    operations = [
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
                ("age_max", models.PositiveIntegerField(null=True)),
                (
                    "amount_min",
                    models.FloatField(
                        help_text="Use of the amount fields differs depending on the selected <em>dri_type</em>.</br>* AMDR - <em>amount_min</em> and <em>amount_max</em> are the lower and the upper limits of the range respectively.</br>* AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - <em>amount_min</em> is the RDA or AI value. <em>amount_max</em> is the UL value (if available).</br>* AIK - use only <em>amount_min</em>.</br>* UL - uses only <em>amount_max</em>.</br>* ALAP - ignores both.",
                        null=True,
                    ),
                ),
                ("amount_max", models.FloatField(null=True)),
                (
                    "nutrient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommendations",
                        to="main.nutrient",
                    ),
                ),
            ],
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
            ],
        ),
        migrations.AddField(
            model_name="nutrient",
            name="types",
            field=models.ManyToManyField(
                related_name="nutrients", to="main.nutrienttype"
            ),
        ),
        migrations.CreateModel(
            name="NutrientEnergy",
            fields=[
                (
                    "nutrient",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="energy",
                        serialize=False,
                        to="main.nutrient",
                    ),
                ),
                ("amount", models.FloatField()),
            ],
            options={
                "verbose_name_plural": "Nutrient energies",
            },
        ),
        migrations.AddConstraint(
            model_name="intakerecommendation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("age_max__isnull", True)),
                fields=("sex", "age_min", "dri_type", "nutrient"),
                name="recommendation_unique_demographic_nutrient_and_type_max_age_null",
            ),
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
                        on_delete=django.db.models.deletion.CASCADE, to="main.nutrient"
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="component_nutrient_components",
                        to="main.nutrient",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="nutrient",
            name="components",
            field=models.ManyToManyField(
                related_name="compounds",
                through="main.NutrientComponent",
                to="main.nutrient",
            ),
        ),
        migrations.AddConstraint(
            model_name="nutrientcomponent",
            constraint=models.CheckConstraint(
                check=models.Q(("component", models.F("target")), _negated=True),
                name="main_nutrientcomponent_compound_nutrient_cant_be_component",
            ),
        ),
        migrations.AddConstraint(
            model_name="nutrientcomponent",
            constraint=models.UniqueConstraint(
                fields=("target", "component"), name="main_nutrientcomponent_unique"
            ),
        ),
    ]
