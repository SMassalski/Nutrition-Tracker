"""Models related to meal / recipe features."""
from typing import Dict

from django.db import models
from django.utils import timezone
from main.models.foods import Ingredient
from main.models.user import User
from util import weighted_dict_sum

__all__ = ["Meal", "MealComponent", "MealComponentAmount", "MealComponentIngredient"]

# Meals and Meal Components
#
# Meals represent portions of eaten food composed of
# one or more MealComponents and hold information on the time it was
# eaten for keeping track of the diet.
#
# MealComponents represent prepared / cooked combinations of Ingredients.
# Calculating the component's nutritional values allows balancing a meal
# by adjusting relative amounts of components in a meal.

# TODO: This needs a redesign


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

        # Divide by 100 because its no longer per 100 g, so now its
        # amount * nutrients per gram
        weights = [amount / 100 for amount in amounts]
        nutrients = [component.nutritional_value() for component in components]
        return weighted_dict_sum(nutrients, weights)


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
