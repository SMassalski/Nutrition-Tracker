"""Command and associated functions for populating nutrient data."""
from typing import Dict

from django.core.management.base import BaseCommand
from main.models import (
    IntakeRecommendation,
    Nutrient,
    NutrientComponent,
    NutrientEnergy,
    NutrientType,
)

from ._data import FULL_NUTRIENT_DATA, NUTRIENT_TYPE_DISPLAY_NAME, NUTRIENT_TYPES

# TODO: Custom data options and a better explanation of the format in
#  the documentation / better way to display it.
#  (Override the constructor)


class Command(BaseCommand):
    """
    Command populating the database with nutrient data required for the
    functioning of the application.
    """

    help = "Populates the database with nutrient data."

    # docstr-coverage: inherited
    def handle(self, *args, **options):

        data = FULL_NUTRIENT_DATA
        create_nutrients()

        names = [nut["name"] for nut in data]
        nutrients = Nutrient.objects.filter(name__in=names)
        nutrient_instances = {nut.name: nut for nut in nutrients}

        create_recommendations(nutrient_instances, data=data)
        create_nutrient_types(nutrient_instances, data=data)
        create_energy(nutrient_instances, data=data)
        create_nutrient_components(nutrient_instances, data=data)


def create_nutrients() -> None:
    """Create and save nutrient entries for important nutrients."""
    nutrient_data = [
        {"name": nut["name"], "unit": nut["unit"]} for nut in FULL_NUTRIENT_DATA
    ]
    instances = [Nutrient(**data) for data in nutrient_data]
    Nutrient.objects.bulk_create(instances, ignore_conflicts=True)


def create_recommendations(
    nutrient_dict: Dict[str, Nutrient], data: list = None
) -> None:
    """Create and save recommendation entries reflecting DRI data.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA.
        If `data` is None, the built-in data will be used.
    """
    data = data or FULL_NUTRIENT_DATA
    recommendation_instances = []
    for nutrient in data:
        for recommendation in nutrient["recommendations"]:
            instance = nutrient_dict.get(nutrient.get("name"))
            if instance is not None:
                recommendation_instances.append(
                    IntakeRecommendation(nutrient=instance, **recommendation)
                )

    IntakeRecommendation.objects.bulk_create(
        recommendation_instances, ignore_conflicts=True
    )


def create_nutrient_types(
    nutrient_dict: Dict[str, Nutrient], data: list = None
) -> None:
    """Create and save nutrient type entries for important nutrients.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA.
        If `data` is None, the built-in data will be used.
    """
    data = data or FULL_NUTRIENT_DATA
    nutrient_type_data = (
        NUTRIENT_TYPES if data is FULL_NUTRIENT_DATA else get_nutrient_types(data)
    )

    # Create NutrientType instances
    type_instances = [
        NutrientType(name=type_, displayed_name=NUTRIENT_TYPE_DISPLAY_NAME.get(type_))
        for type_ in nutrient_type_data
    ]
    NutrientType.objects.bulk_create(type_instances, ignore_conflicts=True)

    # Associate NutrientTypes with Nutrients
    types = {
        type_.name: type_
        for type_ in NutrientType.objects.filter(name__in=nutrient_type_data)
    }
    for nutrient in data:
        for type_ in nutrient["type"]:
            nutrient_instance = nutrient_dict.get(nutrient["name"])
            if nutrient_instance is not None:
                nutrient_instance.types.add(types[type_])


def create_energy(nutrient_dict: Dict[str, Nutrient], data: list = None) -> None:
    """Create and save NutrientEnergy records.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA.
        If `data` is None, the built-in data will be used.
    """
    data = data or FULL_NUTRIENT_DATA
    instances = []
    for nutrient in data:
        energy = nutrient.get("energy")
        if energy is None:
            continue
        nutrient_instance = nutrient_dict.get(nutrient.get("name"))

        instances.append(NutrientEnergy(nutrient=nutrient_instance, amount=energy))

    NutrientEnergy.objects.bulk_create(instances, ignore_conflicts=True)


def create_nutrient_components(
    nutrient_dict: Dict[str, Nutrient], data: list = None
) -> None:
    """Create and save NutrientComponent records.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA.
        If `data` is None, the built-in data will be used.
    """
    instances = []
    data = data or FULL_NUTRIENT_DATA
    for nutrient in data:

        components = nutrient.get("components")
        if components is None:
            continue

        target_instance = nutrient_dict.get(nutrient.get("name"))

        for component in components:
            component_instance = nutrient_dict.get(component)

            if component_instance is not None:
                instances.append(
                    NutrientComponent(
                        target=target_instance,
                        component=component_instance,
                    )
                )

    NutrientComponent.objects.bulk_create(instances, ignore_conflicts=True)


def get_nutrient_types(data: list) -> set:
    """Create a set of nutrient type names in `data`.

    Parameters
    ----------
    data
        A list containing the nutrient information in the same format as
        FULL_NUTRIENT_DATA.

    Returns
    -------
    set
    """
    result = set()
    for nutrient in data:
        for type_ in nutrient["type"]:
            result.add(type_)
    return result
