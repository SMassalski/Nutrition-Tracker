"""Helper functions for the 'loadfdcdata' command."""
from main import models

# noinspection PyProtectedMember
from main.models.foods import update_compound_nutrients
from util import get_conversion_factor

# FDC IDs of the preferred FDC nutrient counterparts (if one exists)
PREFERRED_NONSTANDARD = {
    1232,  # Cysteine
    1106,  # Vitamin A, RAE
    1114,  # Vitamin D (D2 + D3)
    1177,  # Folate, total
}

VITAMIN_K_IDS = {1183, 1184, 1185}

# HELPERS


def handle_nonstandard(
    ingredient: "models.Ingredient",
    nutrient: "models.Nutrient",
    fdc_id: int,
    output_dict: dict,
    amount: float,
    preferred_nutrients: "collections.abc.Container",
    additive_nutrients: "collections.abc.Container",
) -> None:
    """Select the appropriate amount for a non-standard nutrient.

    This function only updates the `output_dict`.

    Non-standard nutrients are handled differently depending on whether
    the nutrients are duplicates or additive.

    Duplicate nutrients have a single nutrient in the app but can
    have multiple records in the FDC database. In such case, the amount
    value is used from either the first encountered record or the record
    indicated in `preferred_nutrients`.

    An additive nutrient here means a single nutrient in the app that is
    composed of multiple nutrients in the FDC database,
    e.g., Vitamin K in the FDC database is stored as
    three different compounds: 'Vitamin K (Menaquinone-4)',
    'Vitamin K (Dihydrophylloquinone)' and 'Vitamin K (phylloquinone)

    Parameters
    ----------
    ingredient
        An instance of the Ingredient for which the amount is being set.
    nutrient
        An instance of the Nutrient of which the amount is being set.
    fdc_id
        The id of the nutrient in the FDC database.
    output_dict
        The dictionary the information will be outputted to.
    amount
        The amount of the `nutrient` in `ingredient`. The value must be
        after unit conversion.
    preferred_nutrients
        The FDC ids of nutrient records to be used over other records
        of the same nutrient.
        This is used to deal with situations where one ingredient has
        amount values for multiple nutrient records.
    additive_nutrients
        The FDC ids of additive nutrients.

    Returns
    -------
    None
    """
    if ingredient not in output_dict:
        output_dict[ingredient] = {}

    # Duplicate
    if nutrient not in output_dict[ingredient]:
        output_dict[ingredient][nutrient] = amount

    elif fdc_id in preferred_nutrients:
        output_dict[ingredient][nutrient] = amount

    # Additive
    elif fdc_id in additive_nutrients:
        output_dict[ingredient][nutrient] += amount


def get_nutrient_conversion_factors(units: dict, nutrients: dict) -> dict:
    """Get the conversion factors needed for adding nutrient amounts.

    Nutrients in the FDC data may use different units than their
    counterparts in the app's database.
    Because of that, when adding IngredientNutrient records from FDC
    data, the amounts need to be adjusted to match local units using
    the dict from this function.

    Parameters
    ----------
    units
        A mapping from nutrient ids, in the FDC data, to its unit.
    nutrients
        A mapping from nutrient names to their instances.

    Returns
    -------
    dict
    """
    conversion_factors = {}
    for id_, unit in units.items():
        nut = nutrients.get(id_)
        if nut is not None:
            factor = get_conversion_factor(unit, nut.unit, nut.name)
            conversion_factors[id_] = factor

    return conversion_factors


class NoNutrientException(Exception):
    """
    Raised when the nutrients required for a process are not present
    in the database.
    """


def create_compound_nutrient_amounts():
    """Create IngredientNutrient instances for compound nutrients."""
    nutrients = models.Nutrient.objects.filter(components__isnull=False)
    ingredient_nutrients = []
    for nut in nutrients:
        ingredient_nutrients += update_compound_nutrients(nut, commit=False)

    models.IngredientNutrient.objects.bulk_create(
        ingredient_nutrients,
        update_conflicts=True,
        update_fields=["amount"],
        unique_fields=["ingredient", "nutrient"],
    )


def get_fdc_data_source() -> models.FoodDataSource:
    """Get or create a FoodDataSource record for USDA's Food Data Central."""
    return models.FoodDataSource.objects.get_or_create(name="FDC")[0]
