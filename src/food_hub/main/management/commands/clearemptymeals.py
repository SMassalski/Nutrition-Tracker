"""
Command for removing Meal entries without any related MealIngredients.
"""
from django.contrib.sessions.models import Session
from django.core.management import BaseCommand
from django.db.models import Q
from main.models import Meal


class Command(BaseCommand):
    """
    Command for removing Meal entries without any related
    MealIngredients.

    Meals that are a session's current meal will not be removed.
    """

    help = (
        "Remove Meal entries without any related MealIngredients. Meals that are "
        "a session's current meal will not be removed."
    )

    # docstr-coverage: inherited
    def handle(self, *args, **options):

        sessions = Session.objects.all()
        meal_ids = [session.get_decoded().get("meal_id") for session in sessions]
        meal_ids = [id_ for id_ in meal_ids if id_ is not None]

        Meal.objects.filter(
            ~Q(id__in=meal_ids),
            mealingredient__isnull=True,
            mealrecipe__isnull=True,
        ).delete()
