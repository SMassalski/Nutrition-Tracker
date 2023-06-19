import pytest
from main.models import IntakeRecommendation
from main.serializers import ProfileRecommendationSerializer


class TestProfileRecommendationSerializer:
    """Tests of ProfileRecommendationSerializer"""

    @pytest.fixture(autouse=True)
    def serializer_kwargs(self, profile):
        """
        Default keyword arguments used for serializer construction.
        """
        self.init_kwargs = {
            "context": {"profile": profile},
        }

    def test_profile_amount_min(self, db, recommendation):
        """
        The serializer's profile_amount_min field returns the
        amount_min value of the recommendation adjusted for the profile.
        """
        recommendation.dri_type = IntakeRecommendation.RDAKG

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("profile_amount_min") == 400

    def test_upper_limit(self, db, recommendation):
        """
        The serializer's upper_limit field returns the amount_max value.
        """
        recommendation.amount_max = 10

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("upper_limit") == 10

    def test_upper_limit_none(self, db, recommendation):
        """
        The serializer's upper_limit field returns inf if the
        recommendation doesn't have a UL.
        """
        recommendation.amount_max = None

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("upper_limit") == float("inf")

    def test_displayed_amount(self, db, recommendation):
        """
        The serializer's displayed_amount field returns `amount_min` for
        recommendations with dri_type other than ALAP and UL.
        """
        recommendation.amount_min = 2

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("displayed_amount") == 2

    def test_displayed_amount_alap(self, db, recommendation):
        """
        The serializer's displayed_amount field returns None for
        recommendations with dri_type ALAP.
        """
        recommendation.dri_type = IntakeRecommendation.ALAP

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("displayed_amount") is None

    def test_displayed_amount_ul(self, db, recommendation):
        """
        The serializer's displayed_amount field returns None for
        recommendations with dri_type UL.
        """
        recommendation.dri_type = IntakeRecommendation.UL

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("displayed_amount") == 5

    def test_displayed_amount_rounds_value(self, db, recommendation):
        """
        The serializer's displayed_amount field returns the value
        rounded to the first decimal place.
        """
        recommendation.amount_min = 1.78

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        assert serializer.data.get("displayed_amount") == 1.8

    def test_lists_types_and_names(self, db, recommendation, nutrient_1):
        """
        The serializer's types field returns a list of related
        NutrientType names and their displayed_names.
        """
        nutrient_1.types.create(name="test_type")
        nutrient_1.types.create(name="test_type_2", displayed_name="display name")

        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)

        types = serializer.data.get("types")
        assert types == [("test_type", None), ("test_type_2", "display name")]
