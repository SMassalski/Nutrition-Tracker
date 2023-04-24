"""main app DjangoORM models."""
from typing import Dict

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from util import weighted_dict_sum


# TODO: Unique user email
class User(AbstractUser):
    """Custom user model for future modification."""

    pass


# A profile should not be required to use the app. Recommended intake
# calculations can use assumptions and averages when relevant
# information is not provided.
class Profile(models.Model):
    """
    Represents user information used for calculating intake
    recommendations.
    """

    # TODO: Additional age functionality
    #  * Column for age unit (months / years)
    #  * Column for tracking age (last time age was edited)
    #  * Energy calculations for ages < 3yo
    # Estimated Energy Requirement equation constants and coefficients
    # dependant on age and sex. The physical activity coefficient is
    # additionally dependant on activity level
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
    activity_choices = [
        ("S", "Sedentary"),
        ("LA", "Low Active"),
        ("A", "Active"),
        ("VA", "Very Active"),
    ]
    sex_choices = [
        ("M", "Male"),
        ("F", "Female"),
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

    def save(self, *args, **kwargs):
        """
        Overriden save method that calculates and updates the energy
        requirement field.
        """
        self.energy_requirement = self.calculate_energy()
        super().save(*args, **kwargs)

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
                coeffs = Profile._EER_COEFFS["infant"]
                # This is more granular - in ages [0, 3) the end
                # constant values change every 6 months
                if self.age < 1:
                    coeffs["end_const"] = -100 + 22
                else:
                    coeffs["end_const"] = -100 + 20
            # 3 - 18 yrs old
            else:
                # Boys
                if self.sex == "M":
                    coeffs = Profile._EER_COEFFS["non-adult_M"]
                # Girls
                else:
                    coeffs = Profile._EER_COEFFS["non-adult_F"]

                if self.age < 9:
                    coeffs["end_const"] = 20
                else:
                    coeffs["end_const"] = 25
        # Adults
        else:
            # Men
            if self.sex == "M":
                coeffs = Profile._EER_COEFFS["adult_M"]
            # Women
            else:
                coeffs = Profile._EER_COEFFS["adult_F"]

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


class FoodDataSource(models.Model):
    """Represents a source of nutrient and ingredient data."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Nutrient(models.Model):
    """
    Represents nutrients contained in ingredients.
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

    def __str__(self):
        return f"{self.name} ({self.PRETTY_UNITS.get(self.unit, self.unit)})"


class Ingredient(models.Model):
    """Represents a food ingredient."""

    # Ingredient's id in the data source database
    external_id = models.IntegerField(unique=True, null=True)
    data_source = models.ForeignKey(
        FoodDataSource, on_delete=models.SET_NULL, null=True
    )
    nutrients = models.ManyToManyField(Nutrient, through="IngredientNutrient")

    name = models.CharField(max_length=50)
    dataset = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def nutritional_value(self) -> Dict[Nutrient, float]:
        """
        Create a dict mapping nutrient to its amount in the ingredient.
        """
        return {ig.nutrient: ig.amount for ig in self.ingredientnutrient_set.all()}

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


# TODO: Change amounts if unit changes (use signals probably)
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
                "ingredient", "nutrient", name="unique_ingredient_intermediate_nutrient"
            )
        ]


# Meals and Meal Components
#
# Meals are representations of a portion of eaten food composed of
# one or more MealComponents and hold information on the time it was
# eaten for keeping track of the diet.
#
# MealComponents represent prepared / cooked combinations of Ingredients.
# Calculating the components nutritional values allows balancing a meal
# by adjusting relative amounts of components in a meal.
#
# There might be an issue with multiple nutrient records of the same
# actual nutrient (probably should be okay as long as only one data
# source is used).


class MealComponent(models.Model):
    """Represents a prepared collection of Ingredients."""

    name = models.CharField(max_length=50)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="meal_components", null=True
    )
    final_weight = models.FloatField()

    def __str__(self):
        return self.name

    def nutritional_value(self) -> Dict[int, float]:
        """
        Calculate the aggregate amount of each nutrient in the
        component per 100g.
        """
        ingredients, amounts = zip(
            *[(i.ingredient, i.amount) for i in self.ingredients.all()]
        )
        weights = [amount / self.final_weight for amount in amounts]
        nutrients = [ingredient.nutritional_value() for ingredient in ingredients]
        return weighted_dict_sum(nutrients, weights)


class MealComponentIngredient(models.Model):
    """
    Represents the amount of an ingredient (in grams) in a
    MealComponent.
    """

    meal_component = models.ForeignKey(
        MealComponent, on_delete=models.CASCADE, related_name="ingredients"
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.meal_component.name} - {self.ingredient.name}"

    class Meta:

        constraints = [
            models.UniqueConstraint(
                "meal_component", "ingredient", name="unique_meal_component_ingredient"
            )
        ]


class Meal(models.Model):
    """
    Represents a portion of food composed of one or more MealComponents.
    """

    date = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=50)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="meals", null=True
    )

    def __str__(self):
        return f"{self.name} ({self.date.strftime('%H:%M - %d %b %Y')})"

    def nutritional_value(self):
        """
        Calculate the aggregate amount of each nutrient in the meal.
        """
        components, amounts = zip(
            *[(i.component, i.amount) for i in self.components.all()]
        )
        # Divide by 100 because its no longer per 100g so now its
        # amount * nutrients per gram
        weights = [amount / 100 for amount in amounts]
        nutrients = [component.nutritional_value() for component in components]
        return weighted_dict_sum(nutrients, weights)


class MealComponentAmount(models.Model):
    """
    Represents the amount (in grams) of a meal component in a meal.
    """

    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="components")
    component = models.ForeignKey(MealComponent, on_delete=models.CASCADE)
    amount = models.FloatField()

    class Meta:

        constraints = [
            models.UniqueConstraint("meal", "component", name="unique_meal_component")
        ]
