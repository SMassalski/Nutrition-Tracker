from core import serializers


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
