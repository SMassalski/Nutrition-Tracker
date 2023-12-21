"""Models related to profile functionality."""
from datetime import timedelta
from warnings import warn

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.lookups import LessThanOrEqual
from django.utils import timezone

__all__ = ["Profile", "IntakeRecommendation", "WeightMeasurement"]


# Estimated Energy Requirement equation constants and coefficients
# dependent on age and sex. The physical activity coefficient is
# additionally dependent on activity level
_EER_COEFFS = {
    "infant": dict(
        start_const=0.0,
        age_c=0.0,
        weight_c=89.0,
        height_c=0.0,
        pa_coeffs={"S": 1.0, "LA": 1.0, "A": 1.0, "VA": 1.0},
    ),
    "non-adult_M": dict(
        start_const=88.5,
        age_c=61.9,
        weight_c=26.7,
        height_c=903,
        pa_coeffs={"S": 1.0, "LA": 1.13, "A": 1.26, "VA": 1.42},
    ),
    "non-adult_F": dict(
        start_const=135.3,
        age_c=30.8,
        weight_c=10.0,
        height_c=934,
        pa_coeffs={"S": 1.0, "LA": 1.16, "A": 1.31, "VA": 1.56},
    ),
    "adult_M": dict(
        start_const=662.0,
        age_c=9.53,
        weight_c=15.91,
        height_c=539.6,
        pa_coeffs={"S": 1.0, "LA": 1.11, "A": 1.25, "VA": 1.48},
    ),
    "adult_F": dict(
        start_const=354,
        age_c=6.91,
        weight_c=9.36,
        height_c=726,
        pa_coeffs={"S": 1.0, "LA": 1.12, "A": 1.27, "VA": 1.45},
    ),
}

# A profile should not be required to use the app. Recommended intake
# calculations can use assumptions and averages when relevant
# information is not provided.
class Profile(models.Model):
    """
    Represents user information used for calculating intake
    recommendations.
    """

    # Activity level constants
    SEDENTARY = "S"
    LOW_ACTIVE = "LA"
    ACTIVE = "A"
    VERY_ACTIVE = "VA"

    # Sex constants
    BOTH = "B"  # Used for recommendations
    FEMALE = "F"
    MALE = "M"

    # TODO: Additional age functionality
    #  * Column for age unit (months / years)
    #  * Column for tracking age (last time age was edited)
    #  * Energy calculations for ages < 3yo

    activity_choices = [
        (SEDENTARY, "Sedentary"),
        (LOW_ACTIVE, "Low Active"),
        (ACTIVE, "Active"),
        (VERY_ACTIVE, "Very Active"),
    ]
    sex_choices = [
        (MALE, "Male"),
        (FEMALE, "Female"),
    ]

    age = models.PositiveIntegerField()
    height = models.PositiveIntegerField()  # In centimeters
    weight = models.PositiveIntegerField()  # In kilograms
    activity_level = models.CharField(max_length=2, choices=activity_choices)
    sex = models.CharField(max_length=1, choices=sex_choices)
    energy_requirement = models.PositiveIntegerField()
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user}'s profile"

    def save(self, add_measurement=False, recalculate_weight=False, *args, **kwargs):
        """Save the current instance.

        Overriden save method that calculates and updates the energy
        requirement field and creates a `WeightMeasurement`
        entry if the profile is being created.

        Parameters
        ----------
        add_measurement: bool
            If True, create a new WeightMeasurement entry for the
            profile with the currently set weight.
            A new measurement is always added if the entry is being
            created.
        recalculate_weight: bool
            If True, set the weight to the weight based on measurements
            before saving.
            This happens after a measurement is created
            if `add_measurement` is True.


        """
        adding = self._state.adding
        if not adding:
            if add_measurement:
                self.weight_measurements.create(value=self.weight)
            if recalculate_weight:
                self.weight = self.current_weight

        self.energy_requirement = self.calculate_energy()
        super().save(*args, **kwargs)

        if adding:
            self.weight_measurements.create(value=self.weight)

    def update_weight(self):
        """Update the profile's weight to match the `current_weight."""
        self.weight = self.current_weight
        self.save()

    @property
    def current_weight(self):
        """The weight of the person based on measurements.

        The returned value is the average of all profile's weight
        measurements within a week from the last one.
        """
        last_measurement_time = self.weight_measurements.aggregate(models.Max("time"))[
            "time__max"
        ]

        return self.weight_measurements.filter(
            time__gte=last_measurement_time - timedelta(days=7)
        ).aggregate(models.Avg("value"))["value__avg"]

    # TODO: There may be a better way to do this
    def calculate_energy(self):
        """
        Calculate the Estimated Energy Requirement for the profile.

        The final result is rounded to the closest integer and is given
        in kcal/day.
        """
        # Coefficients and constants
        # Non-adults
        if self.age < 19:
            # Young children and infants (less than 3yrs old)
            if self.age < 3:
                coeffs = _EER_COEFFS["infant"]
                # This is more granular - in ages [0, 3) the end
                # constant values change every 6 months
                if self.age < 1:
                    coeffs["end_const"] = -100 + 22
                else:
                    coeffs["end_const"] = -100 + 20
            # 3 - 18 yrs old
            else:
                # Boys
                if self.sex == Profile.MALE:
                    coeffs = _EER_COEFFS["non-adult_M"]
                # Girls
                else:
                    coeffs = _EER_COEFFS["non-adult_F"]

                if self.age < 9:
                    coeffs["end_const"] = 20
                else:
                    coeffs["end_const"] = 25
        # Adults
        else:
            # Men
            if self.sex == Profile.MALE:
                coeffs = _EER_COEFFS["adult_M"]
            # Women
            else:
                coeffs = _EER_COEFFS["adult_F"]

        start_const = coeffs.get("start_const", 0.0)
        end_const = coeffs.get("end_const", 0.0)
        age_c = coeffs.get("age_c", 0.0)
        weight_c = coeffs.get("weight_c", 0.0)
        height_c = coeffs.get("height_c", 0.0)
        PA = coeffs["pa_coeffs"][self.activity_level]

        # Equation
        result = (
            start_const
            - (age_c * self.age)
            + PA * (weight_c * self.weight + height_c * self.height / 100)
            + end_const
        )

        return round(result)


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
            sex__in=(profile.sex, Profile.BOTH),
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
        (Profile.BOTH, "Both"),
        (Profile.FEMALE, "Female"),
        (Profile.MALE, "Male"),
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
        "Nutrient", on_delete=models.CASCADE, related_name="recommendations"
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
            # AIK is the Adequate Intake per 1000 kcal
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


class WeightMeasurement(models.Model):
    """
    Represents a weight measurement of a person.
    """

    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="weight_measurements"
    )
    value = models.IntegerField(validators=(MinValueValidator(1),))
    time = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "profile", "time", name="unique_%(app_label)s_%(class)s_profile_time"
            )
        ]
