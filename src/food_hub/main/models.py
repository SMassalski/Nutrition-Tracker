"""main app DjangoORM models."""
from typing import Dict

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from util.util import weighted_dict_sum


class User(AbstractUser):
    """Custom user model for future modification."""

    pass


class Nutrient(models.Model):
    """
    Represents a single type of nutrient such as 'protein' or 'Calcium'.
    """

    # Unit constants
    CALORIES = "KCAL"
    GRAMS = "G"
    MILLIGRAMS = "MG"
    MICROGRAMS = "UG"
    INTERNATIONAL_UNITS = "IU"

    # Unit choices for unit field
    UNIT_CHOICES = [
        (CALORIES, "calories"),
        (GRAMS, "grams"),
        (MILLIGRAMS, "milligrams"),
        (MICROGRAMS, "micrograms"),
        (INTERNATIONAL_UNITS, "IU"),
    ]

    # Unit symbols for string representation
    PRETTY_UNITS = {
        CALORIES: "kcal",
        GRAMS: "g",
        MILLIGRAMS: "mg",
        MICROGRAMS: "µg",
        INTERNATIONAL_UNITS: "IU",
    }

    name = models.CharField(max_length=50)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)

    # Nutrient's id in FDC database
    fdc_id = models.IntegerField(unique=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.PRETTY_UNITS.get(self.unit, self.unit)})"


class Ingredient(models.Model):
    """Represents a food ingredient."""

    # Ingredient's id in FDC database
    fdc_id = models.IntegerField(unique=True, null=True)

    name = models.CharField(max_length=50)
    dataset = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def nutritional_value(self) -> Dict[Nutrient, float]:
        """
        Create a dict mapping nutrient to its amount in the ingredient.
        """
        return {ig.nutrient: ig.amount for ig in self.nutrients.all()}

    @property
    def macronutrient_calories(self) -> Dict[Nutrient, float]:
        """
        The amount of calories per macronutrient in 100g of the
        ingredient.
        """
        nutrients = self.nutrients.filter(
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
    """Represents the amount per 100g of a nutrient in an ingredient."""

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="nutrients"
    )
    nutrient = models.ForeignKey(Nutrient, on_delete=models.CASCADE)

    # The amount is per 100g and the unit is defined in `nutrient.unit`
    amount = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "ingredient", "nutrient", name="unique_ingredient_nutrient"
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
