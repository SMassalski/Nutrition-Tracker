"""Models related to meal / recipe features."""
import re
from datetime import date
from typing import Dict

from core.models.nutrient import Nutrient
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, F, OuterRef, Q, Subquery, Sum, When
from django.utils.text import slugify

__all__ = [
    "Meal",
    "MealIngredient",
    "Recipe",
    "MealRecipe",
    "RecipeIngredient",
]


class MealIntakeQuerySet(models.QuerySet):
    """Meal queryset with methods for intake calculations."""

    def date_within(self, date_min=None, date_max=None):
        """Filter meals to only those from a specified date range.

        Parameters
        ----------
        date_min: datetime.date
            The lower limit (inclusive) for dates that will be included
            in the results.
        date_max: datetime.date
            The upper limit (inclusive) for dates that will be included
            in the results.
        """
        queryset = self
        if date_min is not None:
            queryset = queryset.filter(date__gte=date_min)
        if date_max is not None:
            queryset = queryset.filter(date__lte=date_max)

        return queryset

    def alias_ingredient_intakes(self, alias: str = "intake"):
        """
        Assign an alias to the amount of a nutrient from each
        ingredient in the meal.
        """
        return self.alias(
            **{
                alias: F("mealingredient__amount")
                * F("mealingredient__ingredient__ingredientnutrient__amount")
            }
        )

    def annotate_ingredient_nutrient_names(self, alias="nutrient_name"):
        """
        Annotate the nutrient name from each ingredient in the meal.
        """
        return self.annotate(
            **{
                alias: F(
                    "mealingredient__ingredient__ingredientnutrient__nutrient__name"
                )
            }
        )

    def annotate_ingredient_nutrient_ids(self, alias="nutrient_id"):
        """Annotate the nutrient id from each ingredient in the meal."""
        return self.annotate(
            **{alias: F("mealingredient__ingredient__ingredientnutrient__nutrient")}
        )

    def alias_recipe_intakes(self, alias="intake"):
        """
        Assign an alias to the amount of a nutrient from each
        recipe in the meal. Values are not adjusted for the weight of
        the recipe.
        """
        return self.alias(
            **{
                alias: F("mealrecipe__amount")
                * F("mealrecipe__recipe__recipeingredient__amount")
                * F(
                    "mealrecipe__recipe__recipeingredient__ingredient__ingredientnutrient__amount"
                )
            }
        )

    def annotate_recipe_nutrient_names(self, alias="nutrient_name"):
        """Annotate the nutrient name from each recipe in the meal."""
        return self.annotate(
            **{
                alias: F(
                    "mealrecipe__recipe__ingredients__ingredientnutrient__nutrient__name"
                )
            }
        )

    def annotate_recipe_nutrient_ids(self, alias="nutrient_id"):
        """Annotate the nutrient id from each recipe in the meal."""
        return self.annotate(
            **{
                alias: F(
                    "mealrecipe__recipe__ingredients__ingredientnutrient__nutrient"
                )
            }
        )


class Meal(models.Model):
    """Represents the foods eaten in a single day."""

    owner = models.ForeignKey("core.Profile", on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    ingredients = models.ManyToManyField(
        "core.Ingredient", through="core.MealIngredient"
    )
    recipes = models.ManyToManyField("core.Recipe", through="core.MealRecipe")

    objects = MealIntakeQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "owner",
                "date",
                name="meal_unique_profile_date",
            )
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

        recipe = self.recipe_intakes()
        ingredient = self.ingredient_intakes()

        # sum of values by key
        return {
            key: recipe.get(key, 0) + ingredient.get(key, 0)
            for key in {*recipe.keys(), *ingredient.keys()}
        }

    def recipe_intakes(self):
        """Get nutrient intakes from recipes."""

        queryset = (
            self.mealrecipe_set.annotate(
                nutrient=F(
                    "recipe__recipeingredient__ingredient__ingredientnutrient__nutrient"
                )
            )
            .annotate(
                nutrient_amount=F("amount")
                * F("recipe__recipeingredient__amount")
                * F("recipe__recipeingredient__ingredient__ingredientnutrient__amount")
            )
            .values("nutrient", "recipe_id")
            .exclude(nutrient=None)
            .annotate(total=Sum("nutrient_amount"))
        )
        if not queryset:
            return {}

        recipe_queryset = Recipe.objects.filter(id__in=self.recipes.all()).annotate(
            _weight=Case(
                When(final_weight=None, then=Sum("recipeingredient__amount")),
                When(final_weight__isnull=False, then=F("final_weight")),
            )
        )
        recipes = {rec.id: rec for rec in recipe_queryset}
        ret = {}
        for val in queryset:
            recipe_weight = recipes[val["recipe_id"]]._weight
            amount = val["total"] / recipe_weight
            ret[val["nutrient"]] = ret.get(val["nutrient"], 0) + amount

        return ret

    def ingredient_intakes(self):
        """Get nutrient intakes from individual ingredients."""
        queryset = (
            self.mealingredient_set.annotate(
                nutrient_id=F("ingredient__ingredientnutrient__nutrient")
            )
            .alias(
                nutrient_amount=F("amount")
                * F("ingredient__ingredientnutrient__amount")
            )
            .values("nutrient_id")
            # skip if ingredients don't have nutrients
            .filter(nutrient_id__isnull=False)
            .annotate(amount=Sum("nutrient_amount"))
        )

        return {nutrient["nutrient_id"]: nutrient["amount"] for nutrient in queryset}

    @property
    def calorie_ratio(self) -> Dict[str, float]:
        """
        The percent ratio of calories by nutrient in the meal.

        Does not include nutrients that have a parent in either
        a NutrientType or NutrientComponent relationship.
        """
        ret = self.calories
        total = sum(ret.values())
        return {
            k: round(v / total * 100, 1)
            for k, v in sorted(ret.items(), key=lambda x: x[1], reverse=True)
        }

    @property
    def calories(self):
        """The caloric contribution of nutrients.

        Does not include nutrients that have a parent in either
        a NutrientType or NutrientComponent relationship.
        """
        recipe = self.recipe_calories
        ingredient = self.ingredient_calories

        # sum of values by key
        return {
            key: recipe.get(key, 0) + ingredient.get(key, 0)
            for key in {*recipe.keys(), *ingredient.keys()}
        }

    @property
    def recipe_calories(self):
        """The caloric contribution of nutrients from recipes."""

        nutrients = Nutrient.objects.filter(
            ~Q(types__parent_nutrient__isnull=False),
            compounds=None,
            energy__gt=0,
        )
        nutrients = {nut.id: nut for nut in nutrients}

        queryset = (
            self.mealrecipe_set.annotate(
                nutrient=F(
                    "recipe__recipeingredient__ingredient__ingredientnutrient__nutrient"
                )
            )
            .filter(nutrient__in=nutrients)
            .annotate(
                nutrient_amount=F("amount")
                * F("recipe__recipeingredient__amount")
                * F("recipe__recipeingredient__ingredient__ingredientnutrient__amount")
            )
            .values("nutrient", "recipe_id")
            .annotate(total=Sum("nutrient_amount"))
        )
        if not queryset:
            return {}

        recipe_queryset = Recipe.objects.filter(id__in=self.recipes.all()).annotate(
            _weight=Case(
                When(final_weight=None, then=Sum("recipeingredient__amount")),
                When(final_weight__isnull=False, then=F("final_weight")),
            )
        )
        recipes = {rec.id: rec for rec in recipe_queryset}
        ret = {}
        for val in queryset:
            nutrient = nutrients[val["nutrient"]]
            recipe_weight = recipes[val["recipe_id"]]._weight
            energy = val["total"] / recipe_weight * nutrient.energy
            ret[nutrient.name] = ret.get(nutrient.name, 0) + energy

        return ret

    @property
    def ingredient_calories(self):
        """The caloric contribution of nutrients from ingredients."""
        subquery = Nutrient.objects.filter(
            ~Q(types__parent_nutrient__isnull=False),
            compounds=None,
            ingredient=OuterRef("ingredient"),
        )

        queryset = (
            self.mealingredient_set.filter(
                ingredient__nutrients__energy__gt=0,
                ingredient__nutrients__in=Subquery(subquery.values("pk")),
            )
            .annotate(
                energy=F("ingredient__nutrients__energy")
                * F("amount")
                * F("ingredient__ingredientnutrient__amount"),
                nutrient=F("ingredient__nutrients__name"),
            )
            .values("nutrient")
            .annotate(calories=Sum("energy"))
        )
        return {nutrient["nutrient"]: nutrient["calories"] for nutrient in queryset}


class MealIngredient(models.Model):
    """Represents the amount (in grams) of an Ingredient in a Meal."""

    ingredient = models.ForeignKey("Ingredient", on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    amount = models.FloatField(validators=[MinValueValidator(0.1)])

    def __str__(self):
        return f"{self.meal}: {self.ingredient}"


class Recipe(models.Model):
    """Represents a prepared collection of Ingredients."""

    name = models.CharField(max_length=50)
    owner = models.ForeignKey(
        "core.Profile", on_delete=models.CASCADE, related_name="recipes"
    )
    final_weight = models.FloatField(
        validators=[MinValueValidator(0.1)], null=True, blank=True
    )  # In grams
    ingredients = models.ManyToManyField(
        "core.Ingredient", through="core.RecipeIngredient"
    )
    slug = models.SlugField(max_length=50, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint("owner", "slug", name="recipe_unique_owner_slug"),
            models.UniqueConstraint("owner", "name", name="recipe_unique_owner_name"),
        ]

    def __str__(self):
        return self.name

    # docstr-coverage: inherited
    def save(self, *args, **kwargs):
        self.slug = self.get_slug()
        return super().save(*args, **kwargs)

    def get_slug(self):
        """Generate a correct slug based on the recipe's name."""
        base_slug = slugify(self.name)
        pattern = rf"{base_slug}-\d+$"

        if re.compile(pattern).match(self.slug or ""):
            return self.slug

        # Race conditions shouldn't matter as long as
        # users create recipes one at a time
        # because `slug` must be unique only for each `owner`
        queryset = Recipe.objects.filter(owner=self.owner, slug__regex=pattern).values(
            "slug"
        )
        i = max([int(s["slug"].rsplit("-", 1)[1]) for s in queryset]) if queryset else 0

        return f"{base_slug}-{i+1}"

    def nutritional_value(self) -> Dict[int, float]:
        """
        Calculate the aggregate amount of each nutrient in the
        recipe per gram.
        """
        queryset = (
            self.recipeingredient_set.annotate(
                nutrient_id=F("ingredient__ingredientnutrient__nutrient")
            )
            .alias(
                nutrient_amount=F("amount")
                * F("ingredient__ingredientnutrient__amount"),
            )
            .values("nutrient_id")
            .filter(nutrient_id__isnull=False)
            .annotate(total_amount=Sum("nutrient_amount") / self.weight)
        )

        return {
            nutrient["nutrient_id"]: nutrient["total_amount"] for nutrient in queryset
        }

    def get_intakes(self):
        """Calculate the amount of each nutrient in 100g of the recipe.

        Returns
        -------
        dict[int, float]
            Mapping of nutrient ids to their amount in 100g of
            the recipe.
        """
        return {k: v * 100 for k, v in self.nutritional_value().items()}

    @property
    def weight(self):
        """
        The total weight of the recipe which is either the
        `final_weight` value or the sum of the ingredient
        amounts in the recipe.
        """
        return (
            self.final_weight
            or self.recipeingredient_set.aggregate(Sum("amount"))["amount__sum"]
        )

    @property
    def calories(self) -> Dict[str, float]:
        """
        The amount of calories by nutrient in a gram of the
        recipe.

        Does not include nutrients that have a parent in either
        a NutrientType or NutrientComponent relationship.
        """

        # Nutrients that don't have a type with a parent nutrient or
        # a parent compound nutrient.
        subquery = Nutrient.objects.filter(
            ~Q(types__parent_nutrient__isnull=False),
            compounds=None,
            ingredient=OuterRef("ingredient"),
        )

        queryset = (
            self.recipeingredient_set.filter(
                ingredient__nutrients__energy__gt=0,
                ingredient__nutrients__in=Subquery(subquery.values("pk")),
            )
            .annotate(
                energy=F("ingredient__nutrients__energy")
                * F("amount")
                * F("ingredient__ingredientnutrient__amount"),
                nutrient=F("ingredient__nutrients__name"),
            )
            .values("nutrient")
            .annotate(calories=Sum("energy") / self.weight)
        )
        return {nutrient["nutrient"]: nutrient["calories"] for nutrient in queryset}

    @property
    def calorie_ratio(self) -> Dict[str, float]:
        """
        The percent ratio of calories by nutrient in the recipe.

        Does not include nutrients that have a parent in either
        a NutrientType or NutrientComponent relationship.
        """
        ret = self.calories
        total = sum(ret.values())
        return {
            k: round(v / total * 100, 1)
            for k, v in sorted(ret.items(), key=lambda x: x[1], reverse=True)
        }


class RecipeIngredient(models.Model):
    """
    Represents the amount of an ingredient (in grams) in a
    recipe.
    """

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey("core.Ingredient", on_delete=models.CASCADE)
    amount = models.FloatField(validators=[MinValueValidator(0.1)])

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name}"


class MealRecipe(models.Model):
    """
    Represents the amount (in grams) of a recipe in a meal.
    """

    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.FloatField(validators=[MinValueValidator(0.1)])

    # docstr-coverage: inherited
    def clean(self):
        # Check if the MealRecipe owners match.
        if self.meal.owner != self.recipe.owner:
            raise ValidationError("The meal and recipe owners must be the same.")
