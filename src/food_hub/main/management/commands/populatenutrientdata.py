"""Command and associated functions for populating nutrient data."""
from typing import Dict

from django.core.management.base import BaseCommand
from main.models import IntakeRecommendation, Nutrient, NutrientEnergy, NutrientType

from ._data import FULL_NUTRIENT_DATA, NUTRIENT_TYPES


class Command(BaseCommand):
    """
    Command populating the database with nutrient data required for the
    functioning of the application.
    """

    help = "Populates the database with nutrient data."

    # docstr-coverage: inherited
    def handle(self, *args, **options):
        create_nutrients()

        names = [nut["name"] for nut in FULL_NUTRIENT_DATA]
        nutrients = Nutrient.objects.filter(name__in=names)
        nutrient_instances = {nut.name: nut for nut in nutrients}

        create_recommendations(nutrient_instances)
        create_nutrient_types(nutrient_instances)
        create_energy(nutrient_instances)


def create_nutrients() -> None:
    """Create and save nutrient entries for important nutrients."""
    nutrient_data = [
        {"name": nut["name"], "unit": nut["unit"]} for nut in FULL_NUTRIENT_DATA
    ]
    instances = [Nutrient(**data) for data in nutrient_data]
    Nutrient.objects.bulk_create(instances, ignore_conflicts=True)


def create_recommendations(nutrient_dict: Dict[str, Nutrient]) -> None:
    """Create and save recommendation entries reflecting DRI data.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    """
    recommendation_instances = []
    for nutrient in FULL_NUTRIENT_DATA:
        for recommendation in nutrient["recommendations"]:
            instance = nutrient_dict.get(nutrient.get("name"))
            if instance is not None:
                recommendation_instances.append(
                    IntakeRecommendation(nutrient=instance, **recommendation)
                )

    IntakeRecommendation.objects.bulk_create(
        recommendation_instances, ignore_conflicts=True
    )


def create_nutrient_types(nutrient_dict: Dict[str, Nutrient]) -> None:
    """Create and save nutrient type entries for important nutrients.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    """
    NutrientType.objects.bulk_create(
        [NutrientType(name=type_) for type_ in NUTRIENT_TYPES], ignore_conflicts=True
    )
    types = {
        type_.name: type_
        for type_ in NutrientType.objects.filter(name__in=NUTRIENT_TYPES)
    }
    for nutrient in FULL_NUTRIENT_DATA:
        for type_ in nutrient["type"]:
            nutrient_instance = nutrient_dict.get(nutrient["name"])
            if nutrient_instance is not None:
                nutrient_instance.types.add(types[type_])


def create_energy(nutrient_dict: Dict[str, Nutrient]) -> None:
    """Create and save NutrientEnergy records.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    """
    instances = []
    for nutrient in FULL_NUTRIENT_DATA:
        energy = nutrient.get("energy")
        if energy is None:
            continue
        nutrient_instance = nutrient_dict.get(nutrient.get("name"))
        instances.append(NutrientEnergy(nutrient=nutrient_instance, amount=energy))

    NutrientEnergy.objects.bulk_create(instances, ignore_conflicts=True)
