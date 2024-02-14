"""Set Profile.tracked_nutrients related name."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_profile_tracked_nutrients"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="tracked_nutrients",
            field=models.ManyToManyField(
                related_name="tracking_profiles", to="main.nutrient"
            ),
        ),
    ]
