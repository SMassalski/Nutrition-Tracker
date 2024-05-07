import pytest
from core import models, serializers
from django.db import IntegrityError


class TestCurrentMealSerializer:
    def test_creates_meal_entry(self, saved_profile):
        data = {"date": "2022-06-23"}
        serializer = serializers.CurrentMealSerializer(data=data)
        serializer.is_valid()

        meal = serializer.save(owner=saved_profile)

        assert models.Meal.objects.filter(pk=meal.id).exists()

    def test_create_without_raising_error_if_meal_exists(self, meal, saved_profile):
        data = {"date": meal.date}
        serializer = serializers.CurrentMealSerializer(data=data)
        serializer.is_valid()

        try:
            serializer.save(owner=saved_profile)
        except IntegrityError as e:
            pytest.fail(
                f"CurrentMealSerializer caused an IntegrityError "
                f"when calling create() on duplicate meal data. - {e}"
            )
