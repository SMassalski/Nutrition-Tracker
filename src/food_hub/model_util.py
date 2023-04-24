"""
Utility functions for transferring data from Nutrient model
to IntermediateNutrient model.
"""
from django.db.models import Sum
from main.models import (
    IngredientNutrient,
    IntermediateIngredientNutrient,
    IntermediateNutrient,
    Nutrient,
)


def transfer_nutrient_data():
    """
    Transfers data about each ingredient's nutrient amount data
    from using the old nutrient model to the new one.
    """

    # NOTE: These nutrients need to be treated differently
    #   - (I assume) Cysteine is conflated with cystine in the fdc data.
    #   - Vitamin A and Vitamin D can have entries in either or both IU
    #     and micrograms.
    #   - Vitamin B9 (Folate) has entries as total or equivalents (DFE).
    #   - Vitamin K has entries that are different molecules and need
    #     to be summed up.

    nutrient_exceptions = [
        "Cysteine",
        "Vitamin A",
        "Vitamin B9",
        "Vitamin D",
        "Vitamin K",
    ]
    nutrient_list = Nutrient.objects.exclude(internal_nutrient__isnull=True).exclude(
        internal_nutrient__name__in=nutrient_exceptions
    )
    relations = []
    for nutrient in nutrient_list:
        # Grab ingredients and amounts for selected relations, convert
        # units and add nutrient id information.
        values = nutrient.ingredientnutrient_set.values("ingredient_id", "amount")
        nutrient_id = nutrient.internal_nutrient_id
        for v in values:
            amount = v["amount"] * get_conversion_factor(nutrient)
            v.update({"amount": amount, "nutrient_id": nutrient_id})

        # Create IntermediateIngredientNutrient instances.
        relations.extend([IntermediateIngredientNutrient(**v) for v in values])

    # Exceptions for vitamins A, D and B9, and cysteine are handled
    # by get_relations_for_pairs() defined below.
    relations.extend(get_relations_for_pairs("Vitamin A, RAE", "Vitamin A, IU"))
    relations.extend(
        get_relations_for_pairs(
            "Vitamin D (D2 + D3)", "Vitamin D (D2 + D3), International Units"
        )
    )
    relations.extend(get_relations_for_pairs("Folate, total", "Folate, DFE"))
    relations.extend(get_relations_for_pairs("Cysteine", "Cystine"))

    # Vitamin K summation
    vit_k = IntermediateNutrient.objects.filter(name="Vitamin K").first()
    if vit_k is not None:
        nutrients = vit_k.nutrient_set.all()
        # Assumes units are the same for simplicity.
        for n in nutrients:
            assert vit_k.unit == n.unit

        # Grab all related ingredient nutrients and sum them by ingredient.
        ing_nuts = IngredientNutrient.objects.filter(nutrient__in=nutrients)
        values = ing_nuts.values("ingredient_id").annotate(amount=Sum("amount"))

        # Add nutrient id information.
        for v in values:
            v["nutrient_id"] = vit_k.id

        # Create IntermediateIngredientNutrient instances.
        relations.extend([IntermediateIngredientNutrient(**v) for v in values])

    # Save IntermediateIngredientNutrient instances to the database.
    IntermediateIngredientNutrient.objects.bulk_create(relations)


def get_relations_for_pairs(primary_name: str, secondary_name: str):
    """
    Create intermediate relation instances for two competing nutrients.

    Creates (without saving) instances of IntermediateIngredientNutrient
    for a pair of two nutrient records with the same internal nutrient
    prioritizing the nutrient indicated by `primary_name`. Unit
    conversions are applied automatically.

    Parameters
    ----------
    primary_name
        Name of the primary nutrient.
    secondary_name
        Name of the secondary nutrient.

    Returns
    -------
    list
        IntermediateIngredientNutrient instances created for the two
        nutrients.
    """
    result = []
    nutrient_id = None
    primary_nutrient = (
        Nutrient.objects.select_related("internal_nutrient")
        .filter(name=primary_name)
        .first()
    )

    # Creating intermediates without changes in data for the primary
    # nutrient.
    if primary_nutrient is not None:
        nutrient_id = primary_nutrient.internal_nutrient.id

        # Grab ingredients and amounts for selected relations, convert
        # units and add nutrient id information.
        values = primary_nutrient.ingredientnutrient_set.values(
            "ingredient_id", "amount"
        )
        for v in values:
            amount = v["amount"] * get_conversion_factor(primary_nutrient)
            v.update({"nutrient_id": nutrient_id, "amount": amount})

        # Create IntermediateIngredientNutrient instances.
        result.extend([IntermediateIngredientNutrient(**v) for v in values])

    # Intermediates for secondary nutrient.
    secondary_nutrient = Nutrient.objects.filter(name=secondary_name).first()
    if secondary_nutrient is not None:
        secondary_ingredients = secondary_nutrient.ingredientnutrient_set.all()

        if primary_nutrient is None:
            nutrient_id = secondary_nutrient.internal_nutrient_id
        else:
            # Find ingredients where a relation exists with the
            # secondary nutrient but not with the primary.
            primary_ingredients = primary_nutrient.ingredientnutrient_set.all()
            diff = secondary_ingredients.values_list("ingredient").difference(
                primary_ingredients.values_list("ingredient")
            )
            secondary_ingredients = secondary_ingredients.filter(
                ingredient__in=list(*zip(*diff))
            )

        # Grab ingredients and amounts for selected relations, convert
        # units and add nutrient id information.
        values = secondary_ingredients.values("ingredient_id", "amount")
        for v in values:
            amount = v["amount"] * get_conversion_factor(secondary_nutrient)
            v.update({"nutrient_id": nutrient_id, "amount": amount})

        # Create IntermediateIngredientNutrient instances.
        result.extend([IntermediateIngredientNutrient(**v) for v in values])

    return result


def get_conversion_factor(nutrient: Nutrient):
    """
    Get the factor needed to convert the unit of the nutrient to the
    unit of the nutrients `internal nutrient's` unit.
    """
    from_unit = nutrient.unit
    to_unit = nutrient.internal_nutrient.unit

    # skip if units are the same
    if from_unit == to_unit:
        return 1.0

    # 1 of the unit denoted by the `key` == `value` of grams
    gram_conversion_factors = {
        "UG": 1e-6,
        "MG": 0.001,
        "G": 1,
        "IU": {"Vitamin A": 0.3 * 1e-6, "Vitamin D": 0.025 * 1e-6},
    }

    # From nutrient's unit to grams
    if from_unit == "IU":
        f2g = gram_conversion_factors["IU"].get(nutrient.internal_nutrient.name)
    else:
        f2g = gram_conversion_factors.get(from_unit)
    if f2g is None:
        raise ValueError(f"{nutrient}'s unit {from_unit} was not recognized.")

    # From grams to target unit
    if to_unit == "IU":
        g2t = gram_conversion_factors["IU"].get(nutrient.internal_nutrient.name)
    else:
        g2t = gram_conversion_factors.get(to_unit)
    if g2t is None:
        raise ValueError(
            f"{nutrient.internal_nutrient}'s unit {to_unit} was not recognized."
        )

    return f2g / g2t
