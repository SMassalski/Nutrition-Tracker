# Generated by Django 4.1.4 on 2023-06-09 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0015_nutrientcomponent_nutrient_components_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="intakerecommendation",
            name="amount_min",
            field=models.FloatField(
                help_text="Use of the amount fields differs depending on the selected <em>dri_type</em>.</br>* AMDR - <em>amount_min</em> and <em>amount_max</em> are the lower and the upper limits of the range respectively.</br>* AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - <em>amount_min</em> is the RDA or AI value. <em>amount_max</em> is the UL value (if available).</br>* AIK - use only <em>amount_min</em>.</br>* UL - uses only <em>amount_max</em>.</br>* ALAP - ignores both.",
                null=True,
            ),
        ),
    ]
