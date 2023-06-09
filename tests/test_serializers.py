import pytest
from main import models
from main.serializers import ProfileRecommendationSerializer


class TestProfileRecommendationSerializer:
    """Tests of ProfileRecommendationSerializer"""

    init_kwargs = {
        "context": {"profile": models.Profile(weight=80, energy_requirement=2500)},
    }

    @pytest.fixture(autouse=True)
    def _nutrient(self, nutrient_1):
        self.nutrient = nutrient_1

    def test_profile_recommendation_serializer_profile_amount_min(self, db):
        """
        The serializer's profile_amount_min field returns the
        profile_amount_min value of the recommendation.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.RDAKG,
            amount_min=1,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("profile_amount_min") == 80

    def test_profile_recommendation_serializer_upper_limit(self, db):
        """
        The serializer's upper_limit field returns the amount_max value.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.RDA,
            amount_max=1,
            amount_min=2,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("upper_limit") == 1

    def test_profile_recommendation_serializer_upper_limit_none(self, db):
        """
        The serializer's upper_limit field returns inf if the
        recommendation doesn't have a UL.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.AI,
            amount_max=None,
            amount_min=2,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("upper_limit") == float("inf")

    def test_profile_recommendation_serializer_displayed_amount(self, db):
        """
        The serializer's displayed_amount field returns `amount_min` for
        recommendations with dri_type other than ALAP and UL.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.AI,
            amount_max=None,
            amount_min=2,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("displayed_amount") == 2

    def test_profile_recommendation_serializer_displayed_amount_alap(self, db):
        """
        The serializer's displayed_amount field returns None for
        recommendations with dri_type ALAP.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.ALAP,
            amount_max=None,
            amount_min=2,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("displayed_amount") is None

    def test_profile_recommendation_serializer_displayed_amount_ul(self, db):
        """
        The serializer's displayed_amount field returns None for
        recommendations with dri_type UL.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.UL,
            amount_max=2,
            amount_min=1,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("displayed_amount") == 2

    def test_profile_recommendation_serializer_displayed_amount_rounds_value(self, db):
        """
        The serializer's displayed_amount field returns the value
        rounded to the first decimal place.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.RDA,
            amount_min=1.79,
        )
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        assert serializer.data.get("displayed_amount") == 1.8

    def test_profile_recommendation_serializer_types(self, db):
        """
        The serializer's types field returns a list of related
        NutrientType names and their displayed_names.
        """
        recommendation = models.IntakeRecommendation(
            nutrient=self.nutrient,
            dri_type=models.IntakeRecommendation.ALAP,
            amount_max=None,
            amount_min=2,
        )
        self.nutrient.types.create(name="test_type")
        self.nutrient.types.create(name="test_type_2", displayed_name="display name")
        serializer = ProfileRecommendationSerializer(recommendation, **self.init_kwargs)
        types = serializer.data.get("types")
        assert types == [("test_type", None), ("test_type_2", "display name")]
        assert type(types) is list
