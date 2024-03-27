"""Command and associated functions for populating nutrient data.

Notes
-----
The FULL_NUTRIENT_DATA format is as follows:
[
    {
        'name': <nutrient's name>, (Required for nutrient)
        'unit': <nutrient's unit>, (Required for nutrient)
        'energy': <energy provided by the nutrient in kcal/unit>,
        'fdc_ids':
            [<ids of the nutrient in the FDC database>,...],
        'type': [<names of types of the nutrient>],
        'recommendations`: [
            'age_min': <The youngest age the recommendation applies to>
            (Required for recommendation),
            'age_max': <The oldest age the recommendation applies to>,
            'amount_min': <lower limit of the recommendation>,
            'amount_max': <upper limit of the recommendation>,
            'dri_type': <type of the recommendation> (Required for
                recommendations, one of AI, AIK, AI/KG, ALAP, AMDR, RDA,
                RDA/KG, UL),
            'sex': <sex the recommendation applies to> (Required for
                recommendations, one of M, F, B),
        ]
        'components':
            [<names of nutrients this nutrient consists of>,...]
            (Used for compound nutrients),
    }
]

The NUTRIENT_TYPE_DATA is as follows:
{
    <nutrient_type_name>: {
        'displayed_name': <display name of the type>,
        'parent_nutrient': <name of the type's parent nutrient>,
    }
}
"""
from copy import deepcopy
from typing import Dict
from warnings import warn

from django.core.management.base import BaseCommand
from main.models import IntakeRecommendation, Nutrient, NutrientComponent, NutrientType

from ._data import FULL_NUTRIENT_DATA, NUTRIENT_TYPE_DATA


class Command(BaseCommand):
    """Command populating the database with nutrient data."""

    help = "Populates the database with nutrient data."

    def __init__(self, data=None, type_data=None, **kwargs):
        """Command populating the database with nutrient data.

        Parameters
        ----------
        data: list
            Alternative data to be used instead of the built-in data.
            Must be in the FULL_NUTRIENT_DATA format (see module docs).
        type_data: dict
            A dict containing additional data for nutrient types
            (displayed name and parent nutrient) in the same format as
            NUTRIENT_TYPE_DATA.
            If `None` the built-in type data is used.
        kwargs

        Notes
        -----

        """
        super().__init__(**kwargs)
        self.data = data or FULL_NUTRIENT_DATA

        # Don't use 'or' so the user can specify an empty dict.
        self.type_data = type_data if type_data is not None else NUTRIENT_TYPE_DATA

    # docstr-coverage: inherited
    def handle(self, *args, **options):

        create_nutrients(self.data)

        names = [nut["name"] for nut in self.data]
        nutrients = Nutrient.objects.filter(name__in=names)
        nutrient_instances = {nut.name: nut for nut in nutrients}

        create_recommendations(nutrient_instances, self.data)
        create_nutrient_types(nutrient_instances, self.data, self.type_data)
        create_nutrient_components(nutrient_instances, self.data)


def create_nutrients(data: list) -> None:
    """Create and save nutrient entries for important nutrients.

    Parameters
    ----------
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA (see module docs).
    """
    nutrient_data = [
        {k: v for k, v in d.items() if k in ("name", "unit", "energy")} for d in data
    ]
    # nutrient_data = [{"name": nut["name"], "unit": nut["unit"]} for nut in data]
    instances = [Nutrient(**data) for data in nutrient_data]
    Nutrient.objects.bulk_create(instances, ignore_conflicts=True)


def create_recommendations(nutrient_dict: Dict[str, Nutrient], data: list) -> None:
    """Create and save recommendation entries reflecting DRI data.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA (see module docs).
    """
    recommendation_instances = []
    for nutrient in data:
        for recommendation in nutrient["recommendations"]:
            instance = nutrient_dict.get(nutrient["name"])
            if instance is None:
                warn(
                    f"There are no nutrients with the name '{nutrient['name']}' "
                    f"in the `nutrient_dict`. Skipping the recommendation..."
                )
                continue

            recommendation_instances.append(
                IntakeRecommendation(nutrient=instance, **recommendation)
            )

    IntakeRecommendation.objects.bulk_create(
        recommendation_instances, ignore_conflicts=True
    )


def create_nutrient_types(
    nutrient_dict: Dict[str, Nutrient], data: list, type_data: dict = None
) -> None:
    """Create and save nutrient type entries for important nutrients.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA (see module docs).
    type_data
        A dict containing additional data for nutrient types (displayed
        name and parent nutrient) in the same format as
        NUTRIENT_TYPE_DATA (see module docs).
    """
    nutrient_type_data = deepcopy(type_data) if type_data else {}
    nutrient_type_names = get_nutrient_types(data)

    # Replace the parent nutrient values from the nutrient's name to its
    # instance.
    for nutrient_type, info in list(nutrient_type_data.items()):
        if "parent_nutrient" in info:
            try:
                nutrient = nutrient_dict[info["parent_nutrient"]]
            except KeyError:
                warn(
                    f"NutrientType's '{nutrient_type}' parent nutrient "
                    f"'{info['parent_nutrient']}' not found. Skipping assignment."
                )
                nutrient = None
            info["parent_nutrient"] = nutrient

    # Create NutrientType instances
    type_instances = [
        NutrientType(name=type_, **nutrient_type_data.get(type_, {}))
        for type_ in nutrient_type_names
    ]
    NutrientType.objects.bulk_create(type_instances, ignore_conflicts=True)

    # Associate NutrientTypes with Nutrients
    types = {
        type_.name: type_
        for type_ in NutrientType.objects.filter(name__in=nutrient_type_names)
    }
    for nutrient in data:
        for type_ in nutrient["type"]:
            nutrient_instance = nutrient_dict.get(nutrient["name"])
            if nutrient_instance is not None:
                nutrient_instance.types.add(types[type_])


def create_nutrient_components(nutrient_dict: Dict[str, Nutrient], data: list) -> None:
    """Create and save NutrientComponent records.

    Parameters
    ----------
    nutrient_dict
        Mapping of nutrient names to their respective instances.
    data
        A list containing the nutrient information in the same
        format as FULL_NUTRIENT_DATA (see module docs).
    """
    instances = []
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
        FULL_NUTRIENT_DATA (see module docs).

    Returns
    -------
    set
    """
    result = set()
    for nutrient in data:
        for type_ in nutrient["type"]:
            result.add(type_)
    return result
