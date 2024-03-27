"""
Models related to food items, nutritional value and intake
recommendations.
"""
from typing import Dict, List
from warnings import warn

from django.db import models
from util import get_conversion_factor

__all__ = [
    "FoodDataSource",
    "Ingredient",
    "IngredientNutrient",
]


class FoodDataSource(models.Model):
    """Represents a source of nutrient and ingredient data."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Represents a food ingredient."""

    # Ingredient's id in the data source database
    external_id = models.IntegerField(null=True)
    data_source = models.ForeignKey(
        FoodDataSource, on_delete=models.SET_NULL, null=True
    )
    nutrients = models.ManyToManyField("main.Nutrient", through="IngredientNutrient")

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

    def nutritional_value(self) -> Dict["Nutrient", float]:
        """
        Create a dict mapping nutrient to its amount in the ingredient.
        """
        return {ig.nutrient: ig.amount for ig in self.ingredientnutrient_set.all()}

    @property
    def calories(self) -> Dict["Nutrient", float]:
        """
        The amount of calories by nutrient name in a gram of the
        ingredient.

        Does not include nutrients that have a parent in either
        a NutrientType or NutrientComponent relationship.
        """
        # 'filter(nutrient__types_parent_nutrient=None)' would only
        # exclude nutrients that have only types with a parent nutrient.
        queryset = self.ingredientnutrient_set.filter(
            ~models.Q(nutrient__types__parent_nutrient__isnull=False),
            nutrient__energy__gt=0,
            nutrient__compounds=None,
        ).select_related("nutrient")

        return {
            ing_nut.nutrient.name: ing_nut.amount * ing_nut.nutrient.energy
            for ing_nut in queryset
        }

    @property
    def calorie_ratio(self) -> Dict[str, int]:
        """
        The percent ratio of calories by nutrient in the ingredient.

        Does not include nutrients that have a parent in either
        a NutrientType or NutrientComponent relationship.
        """
        ret = self.calories
        total = sum(ret.values())
        return {
            k: round(v / total * 100, 1)
            for k, v in sorted(ret.items(), key=lambda x: x[1], reverse=True)
        }


class IngredientNutrient(models.Model):
    """
    Represents the amount of a nutrient in 100g of an ingredient.
    """

    nutrient = models.ForeignKey("main.Nutrient", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)

    amount = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "ingredient", "nutrient", name="unique_ingredient_nutrient"
            )
        ]

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        self._old_amount = None
        super().__init__(*args, **kwargs)

    # docstr-coverage: inherited
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)

        # Remember the unit saved in the database
        try:
            instance._old_amount = values[field_names.index("amount")]
        except ValueError:
            # If deferred unit doesn't appear in 'field_names'
            instance._old_amount = models.DEFERRED

        return instance

    def save(self, *args, **kwargs) -> None:
        """Save the current instance.

        Overridden method that updates amounts of IngredientNutrients
        related to the compound nutrient of `nutrient`.
        """

        # Get the amount from the database if it was deferred
        if self._old_amount is models.DEFERRED:
            self._old_amount = IngredientNutrient.objects.get(id=self.id).amount

        super().save(*args, **kwargs)

        if self.amount != self._old_amount:
            for compound in self.nutrient.compounds.all():
                update_compound_nutrients(compound)

        self._old_amount = self.amount

    def __str__(self):
        return (
            f"{self.ingredient}: {self.nutrient.name} ({self.amount} "
            f"{self.nutrient.pretty_unit})"
        )


def update_compound_nutrients(
    nutrient: "Nutrient", commit: bool = True
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

    # For each ingredient, taking units into account, calculate the sum
    #  of `nutrient's` component amounts in the ingredient.
    for values in ingredient_nutrient_data:
        amount = ingredient_amounts.get(values["ingredient_id"], 0)
        try:
            amount += values["amount"] * get_conversion_factor(
                values["nutrient__unit"], nutrient.unit
            )
        except ValueError as e:
            if nutrient.CALORIES in (values["nutrient__unit"], nutrient.unit):
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

    # Create the instances
    ing_nut_kwargs = [
        {"ingredient_id": ing, "amount": amount}
        for ing, amount in ingredient_amounts.items()
    ]
    ing_nuts = [
        IngredientNutrient(nutrient=nutrient, **kwargs) for kwargs in ing_nut_kwargs
    ]

    # Save the instances
    if commit:
        IngredientNutrient.objects.bulk_create(
            ing_nuts,
            update_conflicts=True,
            update_fields=["amount"],
            unique_fields=["ingredient", "nutrient"],
        )

    return ing_nuts
