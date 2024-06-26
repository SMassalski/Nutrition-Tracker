"""Models related to profile functionality."""
from datetime import date, timedelta
from warnings import warn

from core.models.nutrient import Nutrient
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg, Case, F, OuterRef, Q, Subquery, Sum, When
from django.db.models.lookups import LessThanOrEqual

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
    tracked_nutrients = models.ManyToManyField(
        "core.Nutrient", related_name="tracking_profiles", blank=True
    )

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
            `recalculate_weight` is ignored if the profile has no weight
            measurements.


        """
        adding = self._state.adding
        if not adding:
            if add_measurement:
                self.weight_measurements.create(value=self.weight)
            if recalculate_weight:
                self.weight = self.current_weight or self.weight

        self.energy_requirement = self.calculate_energy()
        super().save(*args, **kwargs)

        if adding:
            self.weight_measurements.create(value=self.weight)

    def update_weight(self):
        """Update the profile's weight to match the `current_weight."""
        self.weight = self.current_weight
        self.save()

    @property
    def current_weight(self) -> float:
        """The weight of the person based on measurements.

        The returned value is the average of all profile's weight
        measurements within a week from the last one.

        Returns `None` if the profile has no weight measurements

        Returns
        -------
        float
        """
        last_measurement_date = self.weight_measurements.aggregate(models.Max("date"))[
            "date__max"
        ]
        if last_measurement_date is None:
            return None

        return self.weight_measurements.filter(
            date__gte=last_measurement_date - timedelta(days=7)
        ).aggregate(models.Avg("value"))["value__avg"]

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

    def nutrient_intakes_by_date(self, nutrient_id, date_min=None, date_max=None):
        """Get the intakes of a nutrient by date.

        Parameters
        ----------
        nutrient_id: int
            The id of the nutrient.
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """
        recipe = self.nutrient_intakes_from_recipes(nutrient_id, date_min, date_max)
        ingredient = self.nutrient_intakes_from_ingredients(
            nutrient_id, date_min, date_max
        )

        # sum of values by key
        return {
            key: recipe.get(key, 0) + ingredient.get(key, 0)
            for key in {*recipe.keys(), *ingredient.keys()}
        }

    def nutrient_intakes_from_ingredients(
        self, nutrient_id, date_min=None, date_max=None
    ):
        """Get the intakes of a nutrient from ingredients, by date.

        Parameters
        ----------
        nutrient_id: int
            The id of the nutrient.
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """

        queryset = (
            self.meal_set.date_within(date_min, date_max)
            .annotate_ingredient_nutrient_ids()
            .filter(nutrient_id=nutrient_id)
            .alias_ingredient_intakes()
            .annotate(intake=Sum("intake"))
            .values("date", "intake")
        )

        return {meal["date"]: meal["intake"] for meal in queryset}

    def nutrient_intakes_from_recipes(self, nutrient_id, date_min=None, date_max=None):
        """Get the intakes of a nutrient from recipes, by date.

        Parameters
        ----------
        nutrient_id: int
            The id of the nutrient.
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """

        queryset = (
            self.meal_set.date_within(date_min, date_max)
            .annotate_recipe_nutrient_ids("nutrient_id")
            .annotate(
                recipe_id=F("mealrecipe__recipe_id"),
            )
            .filter(nutrient_id=nutrient_id)
            .alias_recipe_intakes()
            .annotate(amount=Sum("intake"))
            .values("date", "amount", "recipe_id")
        )
        if not queryset:
            return {}

        recipe_queryset = self.recipes.annotate(
            _weight=Case(
                When(final_weight=None, then=Sum("recipeingredient__amount")),
                When(final_weight__isnull=False, then=F("final_weight")),
            )
        )
        recipes = {rec.id: rec for rec in recipe_queryset}

        ret = {}
        for val in queryset:
            amount = val["amount"] / recipes[val["recipe_id"]]._weight
            ret[val["date"]] = ret.get(val["date"], 0) + amount

        return ret

    def calories_by_date(self, date_min=None, date_max=None):
        """Get the caloric contribution of nutrients by date.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """
        recipe = self.calories_from_recipes(date_min, date_max)
        ingredient = self.calories_from_ingredients(date_min, date_max)

        # Combine dicts
        ret = {}
        dates = {*recipe.keys(), *ingredient.keys()}
        for date in dates:
            r = recipe.get(date, {})
            i = ingredient.get(date, {})
            ret[date] = {k: r.get(k, 0) + i.get(k, 0) for k in {*r.keys(), *i.keys()}}

        return ret

    def calories_from_ingredients(self, date_min=None, date_max=None):
        """Get the caloric contribution of nutrients from ingredients,
        by date.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """
        nutrients = Nutrient.objects.filter(
            ~Q(types__parent_nutrient__isnull=False),
            compounds=None,
            energy__gt=0,
        ).values("name")
        nutrients = [nutrient["name"] for nutrient in nutrients]

        # Core queryset
        queryset = (
            self.meal_set.date_within(date_min, date_max)
            .annotate_ingredient_nutrient_names("nutrient")
            .alias_ingredient_intakes()
            .filter(nutrient__in=nutrients)
            .alias(
                energy=F(
                    "mealingredient__ingredient__ingredientnutrient__nutrient__energy"
                )
                * F("intake")
            )
            .values("date", "nutrient")
            .annotate(calories=Sum("energy"))
        )

        ret = {}
        for intake in queryset:
            if intake["date"] not in ret:
                ret[intake["date"]] = {}

            ret[intake["date"]][intake["nutrient"]] = intake["calories"]

        return ret

    def calories_from_recipes(self, date_min=None, date_max=None):
        """Get the caloric contribution of nutrients from recipes, by
        date.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """

        nutrients = Nutrient.objects.filter(
            ~Q(types__parent_nutrient__isnull=False),
            compounds=None,
            energy__gt=0,
        ).values("name")
        nutrients = [nutrient["name"] for nutrient in nutrients]

        queryset = (
            self.meal_set.date_within(date_min, date_max)
            .annotate_recipe_nutrient_names("nutrient")
            .annotate(recipe_id=F("mealrecipe__recipe_id"))
            .filter(nutrient__in=nutrients)
            .alias_recipe_intakes()
            .alias(
                nutrient_energy=F("intake")
                * F(
                    "mealrecipe__recipe__recipeingredient__ingredient__ingredientnutrient__nutrient__energy"
                )
            )
            .values("date", "nutrient", "recipe_id")
            .annotate(calories=Sum("nutrient_energy"))
        )
        if not queryset:
            return {}

        recipe_queryset = self.recipes.annotate(
            _weight=Case(
                When(final_weight=None, then=Sum("recipeingredient__amount")),
                When(final_weight__isnull=False, then=F("final_weight")),
            )
        )
        recipes = {rec.id: rec for rec in recipe_queryset}

        ret = {}
        for val in queryset:
            date = val["date"]
            amount = val["calories"] / recipes[val["recipe_id"]]._weight

            if date not in ret:
                ret[date] = {}

            ret[date][val["nutrient"]] = ret[date].get(val["nutrient"], 0) + amount

        return ret

    def weight_by_date(self, date_min=None, date_max=None):
        """Get the average value of weight measurements each day.

        Parameters
        ----------
        date_min: date
            The lower bound of dates to be included in the results.
        date_max: date
            The upper bound of dates to be included in the results.

        Returns
        -------
        Dict[date, float]
        """
        queryset = self.weight_measurements
        if date_min:
            queryset = queryset.filter(date__gte=date_min)
        if date_max:
            queryset = queryset.filter(date__lte=date_max)

        queryset = queryset.values("date").annotate(avg=Avg("value"))
        return {wm["date"]: wm["avg"] for wm in queryset}

    def energy_progress(self, intake):
        """
        The % ratio of the caloric intake to the recommended intake.
        """

        return min(round(100 * intake / self.energy_requirement), 100)

    def ingredient_intakes(self, date_min=None, date_max=None):
        """Get the intakes of nutrients from ingredients, by date.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """
        queryset = (
            self.meal_set.date_within(date_min, date_max)
            .annotate_ingredient_nutrient_ids()
            .exclude(nutrient_id=None)
            .alias_ingredient_intakes()
            .values("nutrient_id", "date")
            .annotate(intake=Sum("intake"))
        )
        ret = {}
        for item in queryset:
            if item["nutrient_id"] not in ret:
                ret[item["nutrient_id"]] = {}

            ret[item["nutrient_id"]][item["date"]] = item["intake"]

        return ret

    def recipe_intakes(self, date_min=None, date_max=None):
        """Get the intakes of nutrients from recipes, by date.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """
        queryset = (
            self.meal_set.date_within(date_min, date_max)
            .annotate_recipe_nutrient_ids("nutrient_id")
            .annotate(
                recipe_id=F("mealrecipe__recipe_id"),
            )
            .exclude(recipe_id=None)
            .alias_recipe_intakes()
            .annotate(amount=Sum("intake"))
            .values("date", "amount", "recipe_id", "nutrient_id")
        )
        if not queryset:
            return {}

        recipe_queryset = self.recipes.annotate(
            _weight=Case(
                When(final_weight=None, then=Sum("recipeingredient__amount")),
                When(final_weight__isnull=False, then=F("final_weight")),
            )
        )
        recipes = {rec.id: rec for rec in recipe_queryset}

        ret = {}
        for item in queryset:
            nutrient = item["nutrient_id"]
            date = item["date"]

            if nutrient not in ret:
                ret[nutrient] = {}

            amount = item["amount"] / recipes[item["recipe_id"]]._weight
            ret[nutrient][date] = ret[nutrient].get(date, 0) + amount

        return ret

    def average_intakes(self, date_min=None, date_max=None):
        """Get the average intakes of nutrients by date.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results

        Returns
        -------
        dict[datetime.date, float]
        """
        recipe = self.recipe_intakes(date_min, date_max)
        ingredient = self.ingredient_intakes(date_min, date_max)

        ret = {}
        nutrients = {*recipe.keys(), *ingredient.keys()}

        for nutrient in nutrients:
            # sum of values by key
            dates = {
                *recipe.get(nutrient, {}).keys(),
                *ingredient.get(nutrient, {}).keys(),
            }
            ret[nutrient] = (
                sum(recipe.get(nutrient, {}).values())
                + sum(ingredient.get(nutrient, {}).values())
            ) / len(dates)

        return ret

    def malnutrition(
        self, date_min=None, date_max=None, threshold=None, recommendations=None
    ):
        """Get the profile's under- and overconsumed nutrients.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results.
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results.
        threshold: float
            The minimum magnitude the malconsumption must reach to be
            included in the results.
            The magnitude is calculated using the following formula:
                magnitude = abs(intake - limit) / limit
        recommendations: QuerySet
            A IntakeRecommendation queryset to use instead of the
            default.
            If None `IntakeRecommendation.objects.for_profile()`
            is used.

        Returns
        -------
        dict
        """
        intakes = self.average_intakes(date_min, date_max)
        recs = recommendations or IntakeRecommendation.objects.for_profile(
            self
        ).select_related("nutrient")

        ret = {}

        for recommendation in recs:
            nutrient = recommendation.nutrient_id
            intake = intakes.get(nutrient)

            if intake is None:
                continue

            amount_min = recommendation.profile_amount_min(self)

            if amount_min:
                under = amount_min - intake
                if under > 0:
                    magnitude = under / amount_min
                    if threshold is None or magnitude >= threshold:
                        ret[nutrient] = magnitude
                    continue

            amount_max = recommendation.profile_amount_max(self)

            if amount_max:
                over = intake - amount_max
                if over > 0:
                    magnitude = over / amount_max
                    if threshold is None or magnitude >= threshold:
                        ret[nutrient] = magnitude

        return ret


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

    Notes
    -----
    Different recommendation types will use the amount fields
    in different ways:
     * AMDR - `amount_min` and amount_max are the lower and the upper
      limits of the range respectively.
     * AI/UL, RDA/UL, AIK, AI/KG, RDA/KG - `amount_min` is the RDA or
      AI value. `amount_max` is the UL value (if available).
     * AIK - uses only `amount_min`
     * UL - uses only `amount_max`
     * ALAP - ignores both.
    """

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
    age_max = models.PositiveIntegerField(null=True, blank=True)
    amount_min = models.FloatField(help_text=amount_help_text, null=True, blank=True)
    amount_max = models.FloatField(null=True, blank=True)

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

    # docstr-coverage: inherited
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._profile = None
        self._intake = None

    def set_up(self, profile, intake=None):
        """Set the profile and intake of the recommendation instance.

        Setting the profile allows access to some properties instead of
        accessing the values using a method with the profile and intake
        as a parameter.

        Parameters
        ----------
        profile: Profile
        intake: float
        """
        self._profile = profile
        self._intake = intake

    @property
    def displayed_amount(self) -> float:
        """The displayed amount for a recommendation.

        The field used differs between dri_types.
        """
        if self._profile is None:
            raise AttributeError(
                "You must set the recommendation's profile to use the "
                "`displayed_amount` property. The profile can be set "
                "using the `set_up()` method"
            )

        if self.dri_type == IntakeRecommendation.ALAP:
            return None
        elif self.dri_type == IntakeRecommendation.UL:
            amount = self.profile_amount_max(self._profile)
        else:
            amount = self.profile_amount_min(self._profile)

        return amount

    @property
    def over_limit(self) -> bool:
        """
        Whether the nutrient's intake is higher than or equal to the
        recommended upper limit.

        Returns `False` if intake was not provided.
        """
        if self._profile is None:
            raise AttributeError(
                "You must set the recommendation's profile to use"
                " the `over_limit` property. The profile can be set "
                "using the `set_up()` method"
            )

        limit = self.profile_amount_max(self._profile) or float("inf")

        if self._intake is None:
            return False
        return self._intake >= limit

    @property
    def progress(self) -> int:
        """
        The ratio of the nutrient intake to the recommended nutrient
        intake in percent.

        Returns `None` if intake was not provided.
        """
        if self._profile is None:
            raise AttributeError(
                "You must set the recommendation's profile to use"
                " the `progress` property. The profile can be set "
                "using the `set_up()` method"
            )

        if self.dri_type == IntakeRecommendation.UL:
            target = self.profile_amount_max(self._profile)
        else:
            target = self.profile_amount_min(self._profile)

        try:
            progress = min(round(100 * self._intake / target), 100)
        except (TypeError, ZeroDivisionError):
            # Recommendation's amount min is 0 or the intake is None
            # because no meal was provided in the context.
            progress = None

        return progress

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
                    amount * profile.energy_requirement / (self.nutrient.energy * 100.0)
                )
            except ZeroDivisionError:
                warn(
                    f"Nutrient with an AMDR recommendation: {self.nutrient} has "
                    f"an energy value of 0. "
                    f"Some of the displayed information may be inaccurate."
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
    value = models.FloatField(validators=(MinValueValidator(0.1),))
    date = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.date}: {self.value}"

    # docstr-coverage: inherited
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.profile.save(recalculate_weight=True)
