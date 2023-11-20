"""Models related to meal / recipe features."""
from typing import Dict

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from main.models.foods import Ingredient, IngredientNutrient
from main.models.user import User
from util import weighted_dict_sum

__all__ = [
    "Meal",
    "MealComponent",
    "MealComponentAmount",
    "MealComponentIngredient",
    "MealIngredient",
]

# Meals and Meal Components
#
# Meals represent portions of eaten food composed of
# one or more MealComponents and hold information on the time it was
# eaten for keeping track of the diet.
#
# MealComponents represent prepared / cooked combinations of Ingredients.
# Calculating the component's nutritional values allows balancing a meal
# by adjusting relative amounts of components in a meal.


class Meal(models.Model):
    """Represents the foods eaten in a single day."""

    owner = models.ForeignKey("main.Profile", on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    ingredients = models.ManyToManyField("Ingredient", through="main.MealIngredient")

    class Meta:
        constraints = [
            models.UniqueConstraint("owner", "date", name="meal_unique_profile_date")
        ]

    def __str__(self):
        return f"{self.owner.user.username} ({self.date.strftime('%d %b %Y')})"

    def get_intakes(self):
        """Calculate the amount of each nutrient in the meal.

        Returns
        -------
        dict[int, float]
            Mapping of nutrient ids to their amount in the meal.
        """

        # Grab each ingredient and its amount in the meal.
        queryset = self.mealingredient_set.values_list("ingredient_id", "amount")
        ingredient_amounts = {}
        for id_, amount in queryset:
            ingredient_amounts[id_] = ingredient_amounts.get(id_, 0) + amount

        # Grab the amount of each nutrient in the ingredients.
        nutrient_amounts = IngredientNutrient.objects.filter(
            ingredient_id__in=ingredient_amounts.keys()
        ).values_list("nutrient_id", "ingredient_id", "amount")

        # Combine the nutrient amounts.
        result = {}
        for nutrient, ingredient, amount in nutrient_amounts:
            result[nutrient] = (
                result.get(nutrient, 0) + amount * ingredient_amounts[ingredient]
            )

        return result


class MealIngredient(models.Model):
    """Represents the amount (in grams) of an Ingredient in a Meal."""

    ingredient = models.ForeignKey("Ingredient", on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    amount = models.FloatField(validators=[MinValueValidator(0.1)])

    def __str__(self):
        return f"{self.meal}: {self.ingredient}"


# NOTE: Ignore the stuff below for now.


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
