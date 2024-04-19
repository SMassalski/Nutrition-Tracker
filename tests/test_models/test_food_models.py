"""
Tests of models related to food items, nutritional value and intake
recommendations.
"""
import pytest
from django.db import IntegrityError
from main import models

# noinspection PyProtectedMember
from main.models.foods import update_compound_nutrients


class TestIngredient:
    """Tests of the Ingredient model."""

    def test_ingredient_nutritional_value_returns_nutrient_amounts(
        self, ingredient_1, ingredient_nutrient_1_1, ingredient_nutrient_1_2
    ):
        """
        Ingredient.nutritional_value() returns a mapping of nutrients in the ingredient
        to their amounts in the ingredient.
        """
        result = ingredient_1.nutritional_value()
        assert (
            result[ingredient_nutrient_1_1.nutrient] == ingredient_nutrient_1_1.amount
        )
        assert (
            result[ingredient_nutrient_1_2.nutrient] == ingredient_nutrient_1_2.amount
        )

    def test_ingredient_calories_calculates_energies_in_ingredient(
        self, ingredient_1, nutrient_1, ingredient_nutrient_1_1, nutrient_1_energy
    ):
        # ingredient_nutrient_1_1 amount * nutrient_1_energy amount
        expected = 1.5 * 10
        assert ingredient_1.calories == {nutrient_1.name: expected}

    def test_ingredient_calories_only_returns_nutrients_with_energy(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
    ):
        result = ingredient_1.calories

        assert nutrient_1.name in result
        assert nutrient_2.name not in result

    def test_calories_excludes_component_nutrients(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        nutrient_1_energy,
        component,
    ):

        result = ingredient_1.calories

        assert nutrient_1.name not in result

    def test_calories_excludes_child_type_nutrients(
        self,
        ingredient_1,
        nutrient_1,
        ingredient_nutrient_1_1,
        nutrient_2,
        nutrient_1_energy,
    ):
        type_ = models.NutrientType.objects.create(parent_nutrient=nutrient_2)
        nutrient_1.types.add(type_)

        result = ingredient_1.calories

        assert nutrient_1.name not in result

    def test_ingredient_calorie_ratio_is_percent_caloric_contribution_of_nutrients(
        self,
        ingredient_1,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        nutrient_2_energy,
    ):
        expected = {nutrient_1.name: 97.4, nutrient_2.name: 2.6}

        actual = ingredient_1.calorie_ratio

        assert actual == expected

    def test_ingredient_calorie_ratio_is_sorted_by_values_descending(
        self,
        ingredient_1,
        nutrient_1,
        nutrient_2,
        ingredient_nutrient_1_1,
        ingredient_nutrient_1_2,
        nutrient_1_energy,
        nutrient_2_energy,
    ):
        expected = [97.4, 2.6]

        actual = list(ingredient_1.calorie_ratio.values())

        assert actual == expected

    def test_calorie_ratio_no_calories_doesnt_divide_by_zero(
        self,
        ingredient_1,
        nutrient_1_energy,
        ingredient_nutrient_1_1,
    ):
        ingredient_nutrient_1_1.amount = 0
        ingredient_nutrient_1_1.save()

        try:
            _ = ingredient_1.calorie_ratio

        except ZeroDivisionError:
            pytest.fail(
                "Ingredient.calorie_ratio raised ZeroDivision, for an"
                "ingredient that doesn't have any caloric nutrients."
            )

    def test_calorie_ratio_no_caloric_nutrients_returns_calories(
        self,
        ingredient_1,
        nutrient_1_energy,
        ingredient_nutrient_1_1,
    ):
        ingredient_nutrient_1_1.amount = 0
        ingredient_nutrient_1_1.save()

        assert ingredient_1.calorie_ratio == {"test_nutrient": 0}  # ingredient.calories


# noinspection PyUnusedLocal
class TestIntakeRecommendation:
    """Tests of the IntakeRecommendation model."""

    @pytest.fixture
    def amdr_recommendation(self, recommendation):
        """
        An unsaved IntakeRecommendation instance with `dri_type='AMDR'.

        dri_type: "AMDR"
        amount_min: 5.0
        amount_max: 5.0
        nutrient: nutrient_1
        """
        recommendation.dri_type = models.IntakeRecommendation.AMDR
        return recommendation

    @pytest.mark.parametrize(
        "dri_type,expected",
        [
            (models.IntakeRecommendation.AIK, 10.0),
            (models.IntakeRecommendation.AIKG, 400.0),
            (models.IntakeRecommendation.RDAKG, 400.0),
        ],
    )
    def test_profile_amount_min(self, dri_type, expected, profile):
        """
        IntakeRecommendation.profile_amount_min() returns the
        recommendation's `amount_min` according to it's `dri_type` and
        the profile's `weight` and `energy_requirement` values.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_min=5.0)

        assert recommendation.profile_amount_min(profile) == expected

    @pytest.mark.parametrize(
        "dri_type,expected",
        [
            (models.IntakeRecommendation.AIK, 10.0),
            (models.IntakeRecommendation.AIKG, 400.0),
            (models.IntakeRecommendation.RDAKG, 400.0),
        ],
    )
    def test_profile_amount_max(self, dri_type, expected, profile):
        """
        IntakeRecommendation.profile_amount_max() returns the
        recommendation's `amount_max` according to it's `dri_type` and
        the profile's `weight` and `energy_requirement` values.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_max=5.0)

        assert recommendation.profile_amount_max(profile) == expected

    @pytest.mark.parametrize(
        "dri_type",
        [
            models.IntakeRecommendation.AI,
            models.IntakeRecommendation.ALAP,
            models.IntakeRecommendation.RDA,
            models.IntakeRecommendation.UL,
        ],
    )
    def test_profile_amount_min_independent_type(self, dri_type, profile):
        """
        IntakeRecommendation.profile_amount_min() returns the
        recommendation's `amount_min` unchanged if it's `dri_type`
        is independent of profile attributes.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_min=5.0)

        assert recommendation.profile_amount_min(profile) == 5.0

    @pytest.mark.parametrize(
        "dri_type",
        [
            models.IntakeRecommendation.AI,
            models.IntakeRecommendation.ALAP,
            models.IntakeRecommendation.RDA,
            models.IntakeRecommendation.UL,
        ],
    )
    def test_profile_amount_max_independent_type(self, dri_type, profile):
        """
        IntakeRecommendation.profile_amount_max() returns the
        recommendation's `amount_max` unchanged if it's `dri_type`
        is independent of profile attributes.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_max=5.0)

        assert recommendation.profile_amount_max(profile) == 5.0

    def test_profile_amount_min_amdr(self, profile, nutrient_1, amdr_recommendation):
        """
        IntakeRecommendation.profile_amount_min() correctly calculates
        the `amount_min` for recommendations with `dri_type` = 'AMDR'.

        5%(`amount_max`)*2000kcal(`energy_requirement`)/ energy per unit
        """
        nutrient_1.energy = 4
        nutrient_1.save()

        assert amdr_recommendation.profile_amount_min(profile) == 25.0

    def test_profile_amount_max_amdr(self, profile, nutrient_1, amdr_recommendation):
        """
        IntakeRecommendation.profile_amount_max() correctly calculates
        the `amount_max` for recommendations with `dri_type` = 'AMDR'.

        5%(`amount_max`)*2000kcal(`energy_requirement`)/ energy per unit
        """
        nutrient_1.energy = 4
        nutrient_1.save()

        assert amdr_recommendation.profile_amount_max(profile) == 25.0

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_profile_amount_min_amdr_zero_energy(
        self, profile, nutrient_1, amdr_recommendation
    ):
        assert amdr_recommendation.profile_amount_min(profile) == 0

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_profile_amount_max_amdr_no_energy(
        self, profile, nutrient_1, amdr_recommendation
    ):
        assert amdr_recommendation.profile_amount_max(profile) == 0

    def test_profile_amount_min_amdr_no_energy_warns(
        self, profile, nutrient_1, amdr_recommendation
    ):
        with pytest.warns(UserWarning):
            amdr_recommendation.profile_amount_min(profile)

    def test_profile_amount_max_amdr_no_energy_warns(
        self, profile, nutrient_1, amdr_recommendation
    ):
        with pytest.warns(UserWarning):
            amdr_recommendation.profile_amount_max(profile)

    def test_profile_amount_min_none(self, profile, recommendation):
        """
        IntakeRecommendation.profile_amount_min() returns None when
        the `amount_min` is None.
        """
        recommendation.amount_min = None

        assert recommendation.profile_amount_min(profile) is None

    def test_profile_amount_max_none(self, profile, recommendation):
        """
        IntakeRecommendation.profile_amount_max() returns None when
        the `amount_max` is None.
        """
        recommendation.amount_max = None

        assert recommendation.profile_amount_max(profile) is None

    def test_unique_together_constraint_null_age_max(self, nutrient_1):
        """
        IntakeRecommendation unique together constraints take into
        account cases where age_max is None.
        """
        models.IntakeRecommendation.objects.create(
            nutrient=nutrient_1, sex="B", dri_type="ALAP", age_min=0, age_max=None
        )
        with pytest.raises(IntegrityError):
            models.IntakeRecommendation.objects.create(
                nutrient=nutrient_1, sex="B", dri_type="ALAP", age_min=0, age_max=None
            )

    def test_displayed_amount_property_alap(self, profile, recommendation):
        recommendation.dri_type = models.IntakeRecommendation.ALAP
        recommendation.set_up(profile)

        assert recommendation.displayed_amount is None

    def test_displayed_amount_property_ul(self, profile, recommendation):
        recommendation.amount_min = 0
        recommendation.dri_type = models.IntakeRecommendation.UL
        recommendation.set_up(profile)

        assert recommendation.displayed_amount == 5

    @pytest.mark.parametrize(
        ("dri_type", "expected"),
        (
            (models.IntakeRecommendation.AI, 10),
            (models.IntakeRecommendation.AIK, 20),
            (models.IntakeRecommendation.AMDR, 20),
            (models.IntakeRecommendation.RDA, 10),
            (models.IntakeRecommendation.RDAKG, 800),
        ),
    )
    def test_displayed_amount_property_other(
        self, profile, recommendation, dri_type, expected, nutrient_1_energy
    ):
        recommendation.amount_min = 10
        recommendation.amount_max = 20
        recommendation.dri_type = dri_type
        recommendation.set_up(profile)

        assert recommendation.displayed_amount == expected

    def test_displayed_amount_property_not_set_up_raises_error(
        self, profile, recommendation
    ):

        with pytest.raises(AttributeError):
            _ = recommendation.displayed_amount

    def test_progress_property_is_the_percentage_ratio_of_intake_to_profile_amount_min(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_min = 10
        recommendation.set_up(profile, 400)

        assert recommendation.progress == 50

    def test_progress_ul_is_the_percentage_ratio_of_intake_to_profile_amount_max(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.UL
        recommendation.amount_max = 10
        recommendation.set_up(profile, 5)

        assert recommendation.progress == 50

    def test_progress_property_rounded_to_nearest_integer(
        self, profile, recommendation
    ):
        recommendation.amount_min = 9
        recommendation.set_up(profile, 3)

        assert recommendation.progress == 33

    def test_progress_property_capped_at_100(self, profile, recommendation):
        recommendation.amount_min = 5
        recommendation.set_up(profile, 6)

        assert recommendation.progress == 100

    def test_progress_property_returns_none_intake_not_set_up(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_min = 10
        recommendation.set_up(profile)

        assert recommendation.progress is None

    def test_progress_property_returns_none_amount_min_is_none(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_min = None
        recommendation.set_up(profile, 5)

        assert recommendation.progress is None

    def test_progress_property_returns_none_amount_min_zero(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_min = 0
        recommendation.set_up(profile)

        assert recommendation.progress is None

    def test_progress_property_profile_not_set_up_raises_error(
        self, profile, recommendation
    ):
        with pytest.raises(AttributeError):
            _ = recommendation.progress

    def test_over_limit_property_false_if_intake_below_amount_max(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 10
        recommendation.set_up(profile, 10)

        assert recommendation.over_limit is False

    def test_over_limit_property_true_if_intake_equal_amount_max(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 10
        recommendation.set_up(profile, 800)

        assert recommendation.over_limit is True

    def test_over_limit_property_true_if_intake_above_amount_max(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 10
        recommendation.set_up(profile, 801)

        assert recommendation.over_limit is True

    def test_over_limit_property_false_if_amount_max_is_none(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = None
        recommendation.set_up(profile, 801)

        assert recommendation.over_limit is False

    def test_over_limit_property_false_if_intake_not_set_up(
        self, profile, recommendation
    ):
        recommendation.dri_type = models.IntakeRecommendation.RDAKG
        recommendation.amount_max = 10
        recommendation.set_up(profile)

        assert recommendation.over_limit is False

    def test_over_limit_property_raises_error_if_profile_not_set_up(
        self, profile, recommendation
    ):
        with pytest.raises(AttributeError):
            _ = recommendation.over_limit


class TestIntakeRecommendationManager:
    """Tests of IntakeRecommendation's custom manager."""

    @pytest.mark.parametrize(
        ("rec_sex", "expected"), [("B", True), ("F", True), ("M", False)]
    )
    def test_for_profile_by_sex(self, nutrient_1, profile, rec_sex, expected):
        """
        RecommendationQuerySet.for_profile() correctly selects
        IntakeRecommendations matching a profile based on sex.
        """
        # profile.sex = F
        kwargs = {
            "nutrient": nutrient_1,
            "dri_type": models.IntakeRecommendation.ALAP,
            "age_min": 18,
            "age_max": 60,
        }
        models.IntakeRecommendation.objects.create(sex=rec_sex, **kwargs)

        match = models.IntakeRecommendation.objects.for_profile(profile).exists()
        assert match is expected

    @pytest.mark.parametrize(
        ("age_min", "age_max", "expected"),
        [(18, 50, True), (50, 60, True), (20, 30, False)],
    )
    def test_for_profile_by_age(self, nutrient_1, profile, age_min, age_max, expected):
        """
        RecommendationQuerySet.for_profile() correctly selects
        IntakeRecommendations matching a profile based on age.
        """
        # profile.age = 50
        kwargs = {
            "nutrient": nutrient_1,
            "dri_type": models.IntakeRecommendation.ALAP,
            "sex": "F",
        }
        models.IntakeRecommendation.objects.create(
            age_min=age_min, age_max=age_max, **kwargs
        )

        match = models.IntakeRecommendation.objects.for_profile(profile).exists()

        assert match is expected

    def test_for_profile_age_max_is_none(self, nutrient_1):
        """
        RecommendationQuerySet.for_profile() treats recommendations with
        `age_max=None` as a recommendation without an upper age
        limit.
        """
        profile = models.Profile(sex="M", age=999)
        models.IntakeRecommendation.objects.create(
            nutrient=nutrient_1,
            dri_type="UL",
            sex="M",
            age_min=18,
            age_max=None,
        )

        assert models.IntakeRecommendation.objects.for_profile(profile).exists()


class TestUpdateCompoundNutrient:
    """Tests of the update_compound_nutrients() function."""

    def test_clear_old_true_removes_old_ingredient_nutrients(self, compound_nutrient):
        update_compound_nutrients(compound_nutrient)

        update_compound_nutrients(compound_nutrient, commit=False, clear_old=True)
        assert not compound_nutrient.ingredientnutrient_set.exists()

    def test_commit_true(self, compound_nutrient):
        """
        update_compound_nutrients() updates the amounts of
        IngredientNutrients related to a compound nutrient based on the
        amounts of IngredientNutrients related to its component
        nutrients, when `commit` is set to True.
        """
        expected = 3  # component amounts are 1 and 2

        update_compound_nutrients(compound_nutrient, commit=True)

        assert compound_nutrient.ingredientnutrient_set.first().amount == expected

    def test_commit_false(self, compound_nutrient):
        """
        update_compound_nutrients() call with `commits=False` doesn't
        save updated IngredientNutrient records.
        """
        update_compound_nutrients(compound_nutrient, commit=False)

        assert not compound_nutrient.ingredientnutrient_set.exists()

    def test_returns_ingredient_nutrient_list(self, compound_nutrient):
        """
        update_compound_nutrients() call with `commits=False` doesn't
        save updated IngredientNutrient records.
        """
        result = update_compound_nutrients(compound_nutrient, commit=False)

        assert len(result) == 1
        assert isinstance(result[0], models.IngredientNutrient)

    def test_different_compound_unit(self, compound_nutrient):
        """
        update_compound_nutrients() uses unit conversion when
        the components have a different unit than the compound nutrient.
        """
        compound_nutrient.unit = models.Nutrient.MILLIGRAMS
        compound_nutrient.save()

        update_compound_nutrients(compound_nutrient)

        assert compound_nutrient.ingredientnutrient_set.first().amount == 3000

    def test_different_component_unit(self, compound_nutrient):
        """
        update_compound_nutrients() uses unit conversion when
        the components have a different unit than the compound nutrient.
        """
        component = compound_nutrient.components.get(name="component_1")
        component.unit = models.Nutrient.MILLIGRAMS
        component.save()

        update_compound_nutrients(compound_nutrient)

        assert compound_nutrient.ingredientnutrient_set.first().amount == 2.001

    def test_energy_and_weight_unit_mix_warning(self, compound_nutrient):
        """
        update_compound_nutrients() issues a warning if it encounters
        a component relationship where one nutrient has an energy unit
        and the other has a weight unit.
        """
        # Component units are grams.
        compound_nutrient.unit = models.Nutrient.CALORIES
        compound_nutrient.save()

        with pytest.warns(UserWarning):
            update_compound_nutrients(compound_nutrient)

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_energy_and_weight_unit_mix_doesnt_save(self, compound_nutrient):
        """
        update_compound_nutrients() doesn't save IngredientNutrient if
        it encounters a component relationship where one nutrient has an
        energy unit and the other has a weight unit.
        """
        # Component units are grams.
        compound_nutrient.unit = models.Nutrient.CALORIES
        compound_nutrient.save()

        update_compound_nutrients(compound_nutrient)

        assert not compound_nutrient.ingredientnutrient_set.exists()


# noinspection PyUnusedLocal
class TestIngredientNutrient:
    """Tests of the IngredientNutrient model."""

    @pytest.fixture
    def nutrient_2(self, nutrient_2):
        """nutrient_2 fixture with unit changed to grams

        name: nutrient_2
        unit: G
        """
        nutrient_2.unit = models.Nutrient.GRAMS
        nutrient_2.save()

        return nutrient_2

    # NOTE: The IngredientNutrient from the ingredient_nutrient_1_2
    #  fixture is created with the creation of ingredient_nutrient_1_1
    #  or component.
    #  Using the ingredient_nutrient_1_2 fixture will
    #  cause an IntegrityError

    def test_save_updates_amounts_from_db(
        self, component, ingredient_1, nutrient_2, ingredient_nutrient_1_1
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was loaded from the database.
        """
        ingredient_nutrient = models.IngredientNutrient.objects.get(
            pk=ingredient_nutrient_1_1.pk
        )
        ingredient_nutrient.amount = 2
        ingredient_nutrient.save()

        ing_nut_1_2 = models.IngredientNutrient.objects.get(
            ingredient=ingredient_1, nutrient=nutrient_2
        )
        assert ing_nut_1_2.amount == 2

    def test_save_updates_amounts_created(
        self, component, ingredient_1, nutrient_1, ingredient_nutrient_1_2
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was created and saved.
        """
        models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient_1, amount=2
        )

        ingredient_nutrient_1_2.refresh_from_db()
        assert ingredient_nutrient_1_2.amount == 2

    def test_save_updates_amounts_from_db_deferred(
        self, component, ingredient_1, nutrient_2, ingredient_nutrient_1_1
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was loaded from the database,
        but the amount field was deferred.
        """
        ingredient_nutrient = models.IngredientNutrient.objects.defer("amount").get(
            pk=ingredient_nutrient_1_1.pk
        )
        ingredient_nutrient.amount = 2
        ingredient_nutrient.save()

        ing_nut_1_2 = models.IngredientNutrient.objects.get(
            ingredient=ingredient_1, nutrient=nutrient_2
        )
        assert ing_nut_1_2.amount == 2

    def test_delete_updates_compound_ingredient_nutrient(
        self, ingredient_1, nutrient_1, nutrient_2, ingredient_nutrient_1_1, component
    ):
        nutrient_3 = models.Nutrient.objects.create(name="3", unit="G")
        models.NutrientComponent.objects.create(target=nutrient_2, component=nutrient_3)
        models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient_3, amount=10
        )
        ingredient_nutrient_1_1.delete()

        instance = models.IngredientNutrient.objects.get(
            ingredient=ingredient_1, nutrient=nutrient_2
        )
        assert instance.amount == 10

    def test_delete_last_removes_compound_ingredient_nutrient(
        self, ingredient_1, nutrient_1, nutrient_2, ingredient_nutrient_1_1, component
    ):
        ingredient_nutrient_1_1.delete()

        assert not models.IngredientNutrient.objects.filter(
            ingredient=ingredient_1, nutrient=nutrient_2
        ).exists()
