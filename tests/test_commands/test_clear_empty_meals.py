"""Tests of the `clearemptymeals` command."""
from django.contrib.sessions.backends.db import SessionStore
from django.core.management import call_command
from main.models import Meal


class TestCommand:
    def test_removes_empty_meals(self, meal):

        call_command("clearemptymeals")

        assert not Meal.objects.exists()

    def test_keeps_non_empty_meals(self, meal, meal_ingredient):
        call_command("clearemptymeals")

        assert Meal.objects.exists()

    def test_keeps_meals_that_are_in_sessions(self, meal):
        session = SessionStore()
        session["meal_id"] = meal.id
        session.create()

        call_command("clearemptymeals")

        assert Meal.objects.filter(id=meal.id).exists()

    # The MealComponent model needs to be deleted. It causes an extra
    # cascade delete query
    def test_num_queries(self, meal, django_assert_num_queries):

        with django_assert_num_queries(5):
            # 1) Fetch sessions
            # 2) Select meals
            # 3) Cascade delete MealIngredients
            # 4) Cascade delete MealRecipes
            # 4) Delete Meals

            call_command("clearemptymeals")
