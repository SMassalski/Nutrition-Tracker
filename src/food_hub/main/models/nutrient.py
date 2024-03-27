"""The nutrient and related models."""
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property
from util import get_conversion_factor

from .foods import update_compound_nutrients

__all__ = ("Nutrient", "NutrientComponent", "NutrientType")


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
    types = models.ManyToManyField("main.NutrientType", related_name="nutrients")
    components = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="NutrientComponent",
        through_fields=("target", "component"),
        related_name="compounds",
    )
    # Calories per <unit> of the nutrient
    energy = models.FloatField(default=0, validators=(MinValueValidator(0),))

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

        # Remember the unit saved in the database
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
        """The unit's symbols (e.g., µg or kcal)."""
        return self.PRETTY_UNITS[self.unit]

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
        """Save the current instance.

        Modified to update the `amount` of the target's ingredient
        nutrients
        """
        super().save(*args, **kwargs)
        update_compound_nutrients(self.target)

    def __str__(self):
        return f"[{self.target.name}]: {self.component.name}"


class NutrientType(models.Model):
    """
    Represents a type a nutrient might be classified by e.g.,
    Amino acid or Macronutrient.
    """

    name = models.CharField(max_length=32, unique=True)
    displayed_name = models.CharField(max_length=32, null=True)
    parent_nutrient = models.OneToOneField(
        "Nutrient", on_delete=models.SET_NULL, null=True, related_name="child_type"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the current instance.

        The method was modified to prevent hierarchies (NutrientTypes
        can't have a `paren_nutrient` with a type that also has
        a `parent_nutrient`).
        """
        # Prevent saving the NutrientType if the `parent_nutrient`
        # has a type that also has a parent nutrient.
        if self.parent_nutrient is not None:
            parent_nutrient_is_child_type = NutrientType.objects.filter(
                nutrients=self.parent_nutrient, parent_nutrient__isnull=False
            ).exists()
            if parent_nutrient_is_child_type:
                raise NutrientTypeHierarchyError(
                    "`parent_nutrient` can't be of a type that has a `parent_nutrient`."
                )

        super().save(*args, **kwargs)


class CompoundComponentError(ValueError):
    """
    Raised when a compound nutrient is a component of another compound
    nutrient.
    """


class NutrientTypeHierarchyError(ValueError):
    """
    Raised when attempting to save a NutrientType that has a
    `parent_nutrient` with a type that also has a `parent_nutrient`.
    """
