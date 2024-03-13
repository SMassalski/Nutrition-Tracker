import pytest
from django.db import IntegrityError
from main import models, serializers


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


class TestRecipeSerializer:
    def test_creates_recipes_using_request_in_context(self, rf, saved_profile):
        request = rf.get("")
        request.user = saved_profile.user
        data = {"name": "recipe", "final_weight": 1}
        context = {"request": request}
        serializer = serializers.RecipeSerializer(data=data, context=context)
        serializer.is_valid()

        instance = serializer.save()

        assert instance.owner == saved_profile

    def test_validates_unique_together(self, recipe, rf):
        request = rf.get("")
        request.user = recipe.owner.user
        data = {"name": recipe.name, "final_weight": 1}
        context = {"request": request}
        serializer = serializers.RecipeSerializer(data=data, context=context)

        assert not serializer.is_valid()

    def test_doesnt_validate_unique_together_if_name_was_not_changed(self, recipe, rf):
        request = rf.get("")
        request.user = recipe.owner.user
        data = {"name": recipe.name, "final_weight": 1}
        context = {"request": request}
        serializer = serializers.RecipeSerializer(
            instance=recipe, data=data, context=context
        )

        assert serializer.is_valid()
