"""
Models related to food items, nutritional value and intake
recommendations.
"""
from functools import cached_property
from typing import Dict, List
from warnings import warn

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from util import get_conversion_factor

__all__ = [
    "FoodDataSource",
    "Nutrient",
    "NutrientType",
    "NutrientComponent",
    "NutrientEnergy",
    "Ingredient",
    "IngredientNutrient",
]


class FoodDataSource(models.Model):
    """Represents a source of nutrient and ingredient data."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class NutrientType(models.Model):
    """
    Represents a type a nutrient might be classified by e.g.,
    Amino acid or Macronutrient.
    """

    name = models.CharField(max_length=32, unique=True)
    displayed_name = models.CharField(max_length=32, null=True)

    def __str__(self):
        return self.name


class Nutrient(models.Model):
    """
    Represents nutrients contained in ingredients.

    Notes
    -----
    Special consideration should be given when updating the nutrient's
    unit value. The save method updates the amount values of related
    IngredientNutrients, but when using bulk_update() the amounts must
    be changed manually
    """

    # Unit constants
    CALORIES = "KCAL"
    GRAMS = "G"
    MILLIGRAMS = "MG"
    MICROGRAMS = "UG"

    # Unit choices for unit field
    UNIT_CHOICES = [
        (CALORIES, "calories"),
        (GRAMS, "grams"),
        (MILLIGRAMS, "milligrams"),
        (MICROGRAMS, "micrograms"),
    ]

    # Unit symbols for string representation
    PRETTY_UNITS = {
        CALORIES: "kcal",
        GRAMS: "g",
        MILLIGRAMS: "mg",
        MICROGRAMS: "µg",
    }

    name = models.CharField(max_length=32, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    types = models.ManyToManyField(NutrientType, related_name="nutrients")
    components = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="NutrientComponent",
        through_fields=("target", "component"),
        related_name="compounds",
    )

    # NOTE: `from_db()` and `save()` method overrides to update amount values
    #   of related IngredientNutrient records so the actual amount
    #   remains unchanged (when changing unit from grams to milligrams
    #   the amounts are multiplied x 1000)

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        self._old_unit = None
        super().__init__(*args, **kwargs)

    # docstr-coverage: inherited
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)

        # Remember the unit that is saved in the database
        try:
            instance._old_unit = values[field_names.index("unit")]
        except ValueError:
            # If deferred unit doesn't appear in 'field_names'
            instance._old_unit = models.DEFERRED

        return instance

    def save(self, update_amounts: bool = False, *args, **kwargs) -> None:
        """Save the current instance.

        Overridden method to allow amount updates.

        Parameters
        ----------
        update_amounts
            Whether to update the amount values of related
            IngredientNutrient records when changing the nutrient's unit
            so that the actual amount remains unchanged.
        args
            Arguments passed to the base save method.
        kwargs
            Keyword arguments passed to the base save method.
        """
        # If old_unit is None don't update the amounts.
        old_unit = self._old_unit or self.unit

        # Get the unit from the database if it was deferred
        if old_unit is models.DEFERRED:
            old_unit = Nutrient.objects.values("unit").get(id=self.id)["unit"]

        super().save(*args, **kwargs)

        update_amounts = (
            update_amounts and not self._state.adding and self.unit != old_unit
        )

        if update_amounts:
            factor = get_conversion_factor(old_unit, self.unit, self.name)
            self.ingredientnutrient_set.update(amount=models.F("amount") * factor)
            self.recommendations.update(
                amount_min=models.F("amount_min") * factor,
                amount_max=models.F("amount_max") * factor,
            )

        self._old_unit = self.unit

    def __str__(self):
        return f"{self.name} ({self.PRETTY_UNITS.get(self.unit, self.unit)})"

    @property
    def pretty_unit(self) -> str:
        """The unit's symbols (e.g. µg or kcal)."""
        return self.PRETTY_UNITS[self.unit]

    @cached_property
    def energy_per_unit(self) -> float:
        """The amount of energy per unit provided by the nutrient.

        Requires an additional database query if not prefetched
        """
        try:
            return self.energy.amount
        except ObjectDoesNotExist:
            return 0

    @property
    def is_compound(self) -> bool:
        """
        Whether the nutrient consists of one or more component
        nutrients.
        """
        return self.components.exists()

    @property
    def is_component(self) -> bool:
        """
        Whether the nutrient is a component of a compound nutrient.
        """
        return self.compounds.exists()


# TODO:
#  IngredientNutrient amounts of compound nutrients change in two
#  save methods:
#   - IngredientNutrient (optional, not by default)
#   - NutrientComponent (always)
#  This can cause surprising behaviors depending on the order of
#  operations.


class NutrientComponent(models.Model):
    """
    Represents a compound - component relationship between nutrients.
    """

    target = models.ForeignKey(
        Nutrient, on_delete=models.CASCADE, related_name="component_nutrient_components"
    )
    component = models.ForeignKey(Nutrient, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(component=models.F("target")),
                name="%(app_label)s_%(class)s_compound_nutrient_cant_be_component",
            ),
            models.UniqueConstraint(
                fields=("target", "component"), name="%(app_label)s_%(class)s_unique"
            ),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        update_compound_nutrients(self.target)

    def __str__(self):
        return f"[{self.target.name}]: {self.component.name}"


class Ingredient(models.Model):
    """Represents a food ingredient."""

    # Ingredient's id in the data source database
    external_id = models.IntegerField(null=True)
    data_source = models.ForeignKey(
        FoodDataSource, on_delete=models.SET_NULL, null=True
    )
    nutrients = models.ManyToManyField(Nutrient, through="IngredientNutrient")

    name = models.CharField(max_length=50)
    dataset = models.CharField(max_length=50, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("data_source", "external_id"),
                name="unique_ingredient_data_source_and_external_id",
            )
        ]

    def __str__(self):
        return self.name

    def nutritional_value(self) -> Dict[Nutrient, float]:
        """
        Create a dict mapping nutrient to its amount in the ingredient.
        """
        return {ig.nutrient: ig.amount for ig in self.ingredientnutrient_set.all()}

    # TODO: This needs an update.
    @property
    def macronutrient_calories(self) -> Dict[Nutrient, float]:
        """
        The amount of calories per macronutrient in 100g of the
        ingredient.
        """
        nutrients = self.ingredientnutrient_set.filter(
            models.Q(nutrient__name__contains="carbohydrate")
            | models.Q(nutrient__name__contains="lipid")
            | models.Q(nutrient__name__contains="protein")
        )
        result = {ing_nut.nutrient.name: ing_nut.amount for ing_nut in nutrients}

        # For consistency
        result = dict(sorted(result.items()))

        for macronutrient in [("carbohydrate", 4), ("protein", 4), ("lipid", 9)]:
            for k, v in result.items():
                if macronutrient[0] in k.lower():
                    result[k] = v * macronutrient[1]
                    break

        return result


class IngredientNutrient(models.Model):
    """
    Represents the amount of a nutrient in 100g of an ingredient.
    """

    nutrient = models.ForeignKey(Nutrient, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)

    amount = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "ingredient", "nutrient", name="unique_ingredient_nutrient"
            )
        ]

    def __init__(self, *args, **kwargs):
        self._old_amount = None
        super().__init__(*args, **kwargs)

    # docstr-coverage: inherited
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)

        # Remember the unit that is saved in the database
        try:
            instance._old_amount = values[field_names.index("amount")]
        except ValueError:
            # If deferred unit doesn't appear in 'field_names'
            instance._old_amount = models.DEFERRED

        return instance

    def save(self, update_amounts: bool = False, *args, **kwargs) -> None:
        """Save the current instance.

        Overridden method to allow amount updates.

        Parameters
        ----------
        update_amounts
            Whether to update the amount values of IngredientNutrient
            records related to the `nutrient`'s compounds when changing
            the amount.
        args
            Arguments passed to the base save method.
        kwargs
            Keyword arguments passed to the base save method.
        """
        # If old_amount is None don't update the amounts.
        old_amount = self._old_amount or self.amount

        # Get the unit from the database if it was deferred
        if old_amount is models.DEFERRED:
            old_amount = IngredientNutrient.objects.get(id=self.id).amount

        super().save(*args, **kwargs)

        update_amounts = (
            update_amounts and not self._state.adding and self.amount != old_amount
        )

        if update_amounts:
            for compound in self.nutrient.compounds.all():
                update_compound_nutrients(compound)

        self._old_amount = self.amount

    def __str__(self):
        return (
            f"{self.ingredient}: {self.nutrient.name} ({self.amount} "
            f"{self.nutrient.pretty_unit})"
        )


class NutrientEnergy(models.Model):
    """
    Represents the amount of energy provided by a nutrient in kcal/unit.
    """

    nutrient = models.OneToOneField(
        Nutrient, on_delete=models.CASCADE, related_name="energy", primary_key=True
    )
    amount = models.FloatField()

    def __str__(self):
        return f"{self.nutrient.name}: {self.amount} kcal/{self.nutrient.pretty_unit}"

    class Meta:
        verbose_name_plural = "Nutrient energies"


def update_compound_nutrients(
    nutrient: Nutrient, commit: bool = True
) -> List[IngredientNutrient]:
    """Update IngredientNutrient amounts for a compound nutrient.

    The amounts are updated to reflect the amounts of the component
    nutrients' amounts.

    Parameters
    ----------
    nutrient
        The compound nutrient to be updated.
    commit
        Whether to save the IngredientNutrient records.

    Returns
    -------
    List[IngredientNutrient]
        The `nutrient`'s IngredientNutrient instances.
    """

    ingredient_nutrient_data = IngredientNutrient.objects.filter(
        nutrient__in=nutrient.components.all()
    ).values("ingredient_id", "nutrient__unit", "amount")

    ingredient_amounts = {}
    for values in ingredient_nutrient_data:
        amount = ingredient_amounts.get(values["ingredient_id"], 0)
        try:
            amount += values["amount"] * get_conversion_factor(
                values["nutrient__unit"], nutrient.unit
            )
        except ValueError as e:
            if Nutrient.CALORIES in (values["nutrient__unit"], nutrient.unit):
                warn(
                    f"Attempted to convert units from {values['nutrient__unit']} "
                    f"to {nutrient.unit} in update_compound_nutrients() call. "
                    f"Nutrient {nutrient} might have an incompatible component "
                    f"nutrient."
                )
                continue
            else:
                raise e
        ingredient_amounts[values["ingredient_id"]] = amount

    ing_nut_kwargs = [
        {"ingredient_id": ing, "amount": amount}
        for ing, amount in ingredient_amounts.items()
    ]

    ing_nuts = [
        IngredientNutrient(nutrient=nutrient, **kwargs) for kwargs in ing_nut_kwargs
    ]
    if commit:
        IngredientNutrient.objects.bulk_create(
            ing_nuts,
            update_conflicts=True,
            update_fields=["amount"],
            unique_fields=["ingredient", "nutrient"],
        )

    return ing_nuts


class CompoundComponentError(ValueError):
    """
    Raised when a compound nutrient is a component of another compound
    nutrient.
    """
