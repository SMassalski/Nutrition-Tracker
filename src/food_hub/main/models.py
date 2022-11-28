"""main app DjangoORM models"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for future modification"""

    pass


class Nutrient(models.Model):
    """
    Represents a single type of nutrient such as 'protein' or 'Calcium'
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

    # docstr-coverage: inherited
    def __str__(self):
        return f"{self.name} ({self.PRETTY_UNITS[self.unit]})"


class Ingredient(models.Model):
    """Represents a food ingredient"""

    # Ingredient's id in FDC database
    fdc_id = models.IntegerField(unique=True, null=True)

    name = models.CharField(max_length=50)
    dataset = models.CharField(max_length=50)

    # docstr-coverage: inherited
    def __str__(self):
        return self.name


class IngredientNutrient(models.Model):
    """Represents the amount per 100g of a nutrient in an ingredient"""

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    nutrient = models.ForeignKey(Nutrient, on_delete=models.CASCADE)

    # The amount is per 100g and the unit is defined in `nutrient.unit`
    amount = models.IntegerField()
