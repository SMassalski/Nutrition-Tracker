"""
Command for populating the database with intake recommendation data.
"""
from django.core.management.base import BaseCommand, CommandError
from main.models import IntakeRecommendation, Nutrient

from ._recommendations import recommendations


class Command(BaseCommand):
    """
    Command for populating the database with intake recommendation data.
    """

    help = "Populate the database with intake recommendation data."

    # docstr-coverage: inherited
    def handle(self, *args, **kwargs):

        nutrients = {nut.name: nut for nut in Nutrient.objects.all()}

        result = []

        for rec in recommendations:

            nutrient = nutrients.get(rec["nutrient"])
            if nutrient is None:
                # This will happen with for 'Methionine + Cysteine' and
                # 'Phenylalanine + Tyrosine'
                continue

            rec = rec.copy()
            rec["nutrient"] = nutrient

            result.append(IntakeRecommendation(**rec))

        if len(result) == 0:
            # The result will be empty only if the required nutrients
            # were not in the database.
            raise CommandError(
                "The required nutrients were not found. Use the "
                "`populatenutrientdata` command to load nutrients."
            )

        IntakeRecommendation.objects.bulk_create(result, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Recommendations saved successfully."))
