"""
Models related to food items, nutritional value and intake
recommendations.
"""
from functools import cached_property
from typing import Dict, List
from warnings import warn

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.lookups import LessThanOrEqual
from main.models.user import Profile
from util import get_conversion_factor

__all__ = [
    "FoodDataSource",
    "Nutrient",
    "NutrientType",
    "NutrientComponent",
    "NutrientEnergy",
    "IntakeRecommendation",
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


class RecommendationQuerySet(models.QuerySet):
    """Manager class for intake recommendations."""

    def for_profile(self, profile: Profile) -> models.QuerySet:
        """Retrieve a queryset of recommendations matching a profile.

        Returns
        -------
        models.Queryset
            Recommendations that match the profile's age and sex.
        """
        return self.filter(
            models.Q(age_max__gte=profile.age) | models.Q(age_max__isnull=True),
            age_min__lte=profile.age,
            sex__in=(profile.sex, "B"),
        )


class IntakeRecommendation(models.Model):
    """
    Represents dietary intake recommendations for a selected
    demographic.
    """

    # NOTE: Different recommendation types will use the amount fields
    #  in different ways:
    #  * AMDR - `amount_min` and amount_max are the lower and the upper
    #   limits of the range respectively.
    #  * AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - `amount_min` is the RDA or
    #   AI value. `amount_max` is the UL value (if available).
    #  * AIK - uses only `amount_min`
    #  * UL - uses only `amount_max`
    #  * ALAP - ignores both.

    AI = "AI"
    AIK = "AIK"
    AIKG = "AI/KG"
    ALAP = "ALAP"
    AMDR = "AMDR"
    RDA = "RDA"
    RDAKG = "RDA/KG"
    UL = "UL"

    type_choices = [
        (AI, "AI/UL"),
        # AI-KCAL is amount/1000kcal Adequate Intake; mainly for fiber
        # intake.
        (AIK, "AI-KCAL"),
        (AIKG, "AI/KG"),
        (ALAP, "As Low As Possible"),
        (AMDR, "AMDR"),
        (RDA, "RDA/UL"),
        (RDAKG, "RDA/KG"),
        (UL, "UL"),
    ]
    sex_choices = [
        ("B", "Both"),
        ("F", "Female"),
        ("M", "Male"),
    ]

    amount_help_text = (
        "Use of the amount fields differs depending on the selected"
        " <em>dri_type</em>.</br>"
        "* AMDR - <em>amount_min</em> and <em>amount_max</em> are the"
        " lower and the upper limits of the range respectively.</br>"
        "* AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - <em>amount_min</em> is "
        "the RDA or AI value. <em>amount_max</em> is the UL value "
        "(if available).</br>"
        "* AIK - use only <em>amount_min</em>.</br>"
        "* UL - uses only <em>amount_max</em>.</br>"
        "* ALAP - ignores both."
    )

    nutrient = models.ForeignKey(
        Nutrient, on_delete=models.CASCADE, related_name="recommendations"
    )
    dri_type = models.CharField(max_length=6, choices=type_choices)
    sex = models.CharField(max_length=1, choices=sex_choices)
    age_min = models.PositiveIntegerField()
    age_max = models.PositiveIntegerField(null=True)
    amount_min = models.FloatField(help_text=amount_help_text, null=True)
    amount_max = models.FloatField(null=True)

    objects = RecommendationQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=LessThanOrEqual(models.F("age_min"), models.F("age_max")),
                name="recommendation_age_min_max",
            ),
            models.CheckConstraint(
                check=LessThanOrEqual(models.F("amount_min"), models.F("amount_max")),
                name="recommendation_amount_min_max",
            ),
            models.UniqueConstraint(
                fields=("sex", "age_min", "age_max", "dri_type", "nutrient"),
                name="recommendation_unique_demographic_nutrient_and_type",
            ),
            models.UniqueConstraint(
                fields=("sex", "age_min", "dri_type", "nutrient"),
                condition=models.Q(age_max__isnull=True),
                name="recommendation_unique_demographic_nutrient_and_type_max_age_null",
            ),
        ]

    def __str__(self):
        return (
            f"{self.nutrient.name} : {self.age_min} - {self.age_max or ''}"
            f" [{self.sex}] ({self.dri_type})"
        )

    def profile_amount_min(self, profile: Profile) -> float:
        """The `amount_min` taking into account the `profile` attributes.

        Recommendations with `dri_type` 'AMDR' and 'AIK' use the
        profile's energy requirement, and 'AI/KG' and 'RDA/KG' use
        the profile's weight.

        Parameters
        ----------
        profile
            The profile for which the amount will be calculated.

        Returns
        -------
        float
        """
        return self._profile_amount(self.amount_min, profile)

    def profile_amount_max(self, profile: Profile) -> float:
        """The `amount_max` taking into account the `profile` attributes.

        Recommendations with `dri_type` 'AMDR' and 'AIK' use the
        profile's energy requirement, and 'AI/KG' and 'RDA/KG' use
        the profile's weight.

        Parameters
        ----------
        profile
            The profile for which the amount will be calculated.

        Returns
        -------
        float
        """
        return self._profile_amount(self.amount_max, profile)

    # DEV_NOTE: Decide whether the energy dependant recommendations use
    #   the recommended or actual energy intake. (currently recommended
    #   is used)
    def _profile_amount(self, amount: float, profile: Profile) -> float:
        """Get the amount for the recommendation type and given profile.

        The amount is calculated for recommendations that depend on
        the person's weight or recommended energy intake.
        If the recommendation is not dependent on any other value, the
        recommendation amounts are left unchanged.

        Parameters
        ----------
        amount
        profile
            The profile for which the amount will be calculated.
        Returns
        -------
        float

        Examples
        --------
        >>> r = IntakeRecommendation(dri_type="RDA/KG")
        >>> r._profile_amount(5.0, Profile(weight=100))
          500.0
        """
        if amount is None:
            return None

        if self.dri_type == IntakeRecommendation.AIK:
            # AIK is Adequate Intake per 1000 kcal
            return amount * profile.energy_requirement / 1000

        elif self.dri_type in (IntakeRecommendation.AIKG, IntakeRecommendation.RDAKG):
            return amount * profile.weight

        elif self.dri_type == IntakeRecommendation.AMDR:
            # AMDR values are in % of energy intake / requirement,
            # so calculations have to take into account the amount of
            # energy provided by the nutrient
            try:
                return (
                    amount
                    * profile.energy_requirement
                    / (self.nutrient.energy_per_unit * 100.0)
                )
            except ZeroDivisionError:
                warn(
                    f"Couldn't find a NutrientEnergy record for a nutrient with an "
                    f"AMDR recommendation: {self.nutrient}. Some of the displayed "
                    f"information ma be inaccurate."
                )
                return 0.0

        return amount


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

    # TODO: This needs an update. (Not in recommendation branch)
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
