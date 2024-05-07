import pytest
from core import serializers


class TestNutrientIntakeSerializer:
    """Tests of the NutrientIntakeSerializer class."""

    @pytest.fixture(autouse=True)
    def serializer_kwargs(self, context):
        """
        Default keyword arguments used for serializer construction.
        """
        self.intakes = {}
        context["intakes"] = self.intakes
        self.init_kwargs = {
            "context": context,
        }

    def test_get_intakes_returns_intake_of_nutrient(self, nutrient_1):
        self.intakes[nutrient_1.id] = 5
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["intake"] == 5

    def test_get_intakes_zero_if_nutrient_not_in_intakes(self, nutrient_1):
        self.intakes = {}
        serializer = serializers.NutrientIntakeSerializer(
            nutrient_1, **self.init_kwargs
        )

        assert serializer.data["intake"] == 0
