"""
Tests of models related to food items, nutritional value and intake
recommendations.
"""
import pytest
from django.db import IntegrityError
from main import models

# noinspection PyProtectedMember
from main.models.foods import NutrientTypeHierarchyError, update_compound_nutrients


@pytest.fixture
def component(nutrient_1, nutrient_2):
    """Component relationship between nutrient_1 and nutrient_2

    target: nutrient_2
    component: nutrient_1
    """
    return models.NutrientComponent.objects.create(
        target=nutrient_2, component=nutrient_1
    )


class TestIngredient:
    """Tests of the Ingredient model."""

    @pytest.fixture()
    def ingredient_1_macronutrients(self, ingredient_1):
        protein = models.Nutrient.objects.create(name="Protein")
        fat = models.Nutrient.objects.create(name="Total lipid (fat)")
        carbs = models.Nutrient.objects.create(name="Carbohydrate, by difference")

        models.IngredientNutrient.objects.bulk_create(
            [
                models.IngredientNutrient(
                    ingredient_id=ingredient_1.id, nutrient_id=protein.id, amount=1
                ),
                models.IngredientNutrient(
                    ingredient_id=ingredient_1.id, nutrient_id=fat.id, amount=2
                ),
                models.IngredientNutrient(
                    ingredient_id=ingredient_1.id, nutrient_id=carbs.id, amount=3
                ),
            ]
        )

        return ingredient_1.macronutrient_calories

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

    def test_ingredient_macronutrient_calories_returns_only_3_macronutrients(
        self,
        ingredient_1_macronutrients,
    ):
        """
        Ingredient.macronutrient_calories returns values only for protein
        fat and carbohydrates.
        """
        result = ingredient_1_macronutrients
        assert len(result.keys()) == 3
        for macronutrient in ["carbohydrate", "lipid", "protein"]:
            assert len([k for k in result.keys() if macronutrient in k.lower()]) == 1

    def test_ingredient_macronutrient_calories_converts_nutrients_to_calories_correctly(
        self,
        ingredient_1_macronutrients,
    ):
        """
        Ingredient.macronutrient_calories calculates calorie amounts
        according to atwater conversion factors (4 kcal/g for protein and
        carbs, 9 kcal/g for fats).
        """
        # Values depend on amounts in ingredient_1_macronutrients
        assert ingredient_1_macronutrients == {
            "Protein": 4,
            "Total lipid (fat)": 18,
            "Carbohydrate, by difference": 12,
        }

    def test_ingredient_macronutrient_calories_returns_a_dict_sorted_by_keys(
        self,
        ingredient_1_macronutrients,
    ):
        """
        Ingredient.macronutrient_calories calculates return dict is sorted
        by keys.
        """
        assert ingredient_1_macronutrients == dict(
            sorted(ingredient_1_macronutrients.items())
        )


class TestNutrient:
    """Tests of the nutrient model."""

    def test_save_updates_amounts_from_db(self, nutrient_1, ingredient_nutrient_1_1):
        """
        Updating a nutrient's unit changes the amount value of related
        IngredientNutrient records so that the actual amount remains
        unchanged.
        Test for when the instance was loaded from the database.
        """
        nutrient = models.Nutrient.objects.get(pk=nutrient_1.id)

        nutrient.unit = "MG"
        nutrient.save(update_amounts=True)

        ingredient_nutrient_1_1.refresh_from_db()
        assert ingredient_nutrient_1_1.amount == 1500

    def test_save_updates_amounts_created(self, nutrient_1, ingredient_nutrient_1_1):
        """
        Updating a nutrient's unit changes the amount value of related
        IngredientNutrient records so that the actual amount remains
        unchanged.
        Test for when the instance was created and saved.
        """
        nutrient_1.unit = "MG"
        nutrient_1.save(update_amounts=True)

        ingredient_nutrient_1_1.refresh_from_db()
        assert ingredient_nutrient_1_1.amount == 1500

    def test_save_updates_amounts_from_db_deferred(
        self, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        Updating a nutrient's unit changes the amount value of related
        IngredientNutrient records so that the actual amount remains
        unchanged.
        Test for when the instance was loaded from the database,
        but the unit field was deferred.
        """
        nutrient = models.Nutrient.objects.defer("unit").get(id=nutrient_1.id)

        nutrient.unit = "MG"
        nutrient.save(update_amounts=True)

        ingredient_nutrient_1_1.refresh_from_db()
        assert ingredient_nutrient_1_1.amount == 1500

    def test_save_update_amounts_false(self, nutrient_1, ingredient_nutrient_1_1):
        """
        Updating a nutrient's unit doesn't change the amount value of related
        IngredientNutrient records if save was called with `update_amounts`
        set to False.
        """
        nutrient_1.unit = "MG"
        nutrient_1.save(update_amounts=False)

        ingredient_nutrient_1_1.refresh_from_db()
        assert ingredient_nutrient_1_1.amount == 1.5

    def test_save_updates_recommendation_amounts(self, nutrient_1):
        """
        Updating a nutrient's unit changes the amount values of related
        IntakeRecommendations records so that the actual amounts remain
        unchanged.
        """
        recommendation = models.IntakeRecommendation.objects.create(
            nutrient=nutrient_1,
            amount_min=1,
            amount_max=1,
            dri_type=models.IntakeRecommendation.RDA,
            sex="B",
            age_min=0,
        )

        nutrient_1.unit = "MG"
        nutrient_1.save(update_amounts=True)

        recommendation.refresh_from_db()
        assert recommendation.amount_min == 1000
        assert recommendation.amount_max == 1000

    def test_save_update_amount_recommendation_none_amounts(self, nutrient_1):
        """
        Updating a nutrient's unit changes the amount values of related
        IntakeRecommendations records so that the actual amounts remain
        unchanged.
        """
        recommendation = models.IntakeRecommendation.objects.create(
            nutrient=nutrient_1,
            amount_min=None,
            amount_max=None,
            dri_type=models.IntakeRecommendation.RDA,
            sex="B",
            age_min=0,
        )

        nutrient_1.unit = "MG"
        nutrient_1.save(update_amounts=True)

        recommendation.refresh_from_db()
        assert recommendation.amount_min is None
        assert recommendation.amount_max is None

    def test_nutrient_energy_per_unit(self, nutrient_1):
        """
        Nutrient.energy_per_unit() returns the amount value of the
        nutrient's related NutrientEnergy record.
        """
        models.NutrientEnergy(nutrient=nutrient_1, amount=5)

        assert nutrient_1.energy_per_unit == 5

    def test_nutrient_energy_per_unit_no_energy(self):
        """
        Nutrient.energy_per_unit() returns 0 if the nutrient doesn't have
        a related NutrientEnergy record.
        """
        assert models.Nutrient().energy_per_unit == 0

    @pytest.mark.parametrize(
        "unit,expected", [("UG", "µg"), ("MG", "mg"), ("G", "g"), ("KCAL", "kcal")]
    )
    def test_nutrient_pretty_unit_property(self, unit, expected):
        """
        Nutrient.pretty_unit property returns the nutrient's unit's symbol.
        """
        assert models.Nutrient(unit=unit).pretty_unit == expected

    def test_nutrient_is_compound(self, nutrient_1, nutrient_2):
        """
        Nutrient's is_component property indicates whether the nutrient
        consists of one or more component nutrients.
        """
        nutrient_1.components.add(nutrient_2)

        assert nutrient_2.is_compound is False
        assert nutrient_1.is_compound is True

    def test_nutrient_is_component(self, nutrient_1, nutrient_2):
        """
        Nutrient's is_component property indicates whether the nutrient
        is a component of a compound nutrient.
        """
        nutrient_1.components.add(nutrient_2)

        assert nutrient_1.is_component is False
        assert nutrient_2.is_component is True


class TestNutrientComponent:
    """Tests of NutrientComponents."""

    def test_nutrient_component_unique_constraint(self, component):
        """
        NutrientComponent has a unique together constraint for the
        target and component fields.
        """
        with pytest.raises(IntegrityError):
            models.NutrientComponent.objects.create(
                target=component.target, component=component.component
            )

    def test_nutrient_component_self_relation_constraint(self, nutrient_1):
        """
        NutrientComponent cannot have the same nutrient as a target and
        as a component.
        """
        with pytest.raises(IntegrityError):
            models.NutrientComponent.objects.create(
                target=nutrient_1, component=nutrient_1
            )

    def test_nutrient_component_save_updates_compound(
        self, ingredient_1, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        NutrientComponent's save() method updates the `target`
        ingredient nutrient amounts.
        """
        nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")

        models.NutrientComponent.objects.create(target=nutrient, component=nutrient_1)

        ing_nut = nutrient.ingredientnutrient_set.get(ingredient=ingredient_1)
        assert ing_nut.amount == 1.5


class TestNutrientType:
    """Tests of the NutrientType model class."""

    def test_save_parent_nutrient_none(self, nutrient_1):
        """
        NutrientTypes save without error if a `parent_nutrient` is None.
        """
        models.NutrientType.objects.create(name="nt", parent_nutrient=nutrient_1)
        # The NutrientType above is created because it might trip up the
        # method by detecting NutrientTypes that are not associated with
        # any nutrients.
        nutrient_type = models.NutrientType(name="test_type")

        try:
            nutrient_type.save()
        except NutrientTypeHierarchyError as e:
            pytest.fail(str(e))

    def test_save_parent_nutrient_hierarchy(self, nutrient_1, nutrient_2):
        """
        The save method raises an exception if the set `parent_nutrient`
        has a type that also has non-null `parent_nutrient`.
        """
        nutrient_type = models.NutrientType.objects.create(
            name="nt", parent_nutrient=nutrient_1
        )
        nutrient_2.types.add(nutrient_type)
        nutrient_2.save()

        new_nutrient_type = models.NutrientType(
            name="test_type", parent_nutrient=nutrient_2
        )

        with pytest.raises(NutrientTypeHierarchyError):
            new_nutrient_type.save()

    def test_save_parent_nutrient_no_hierarchy(self, nutrient_1):
        """
        The save method doesn't raise an exception if a `parent_nutrient`
        is set to a nutrient that has only types with a null
        `parent_nutrient`.
        """
        nutrient_type = models.NutrientType.objects.create(name="nt")
        nutrient_1.types.add(nutrient_type)
        nutrient_1.save()

        new_nutrient_type = models.NutrientType(
            name="test_type", parent_nutrient=nutrient_1
        )

        try:
            new_nutrient_type.save()
        except NutrientTypeHierarchyError as e:
            pytest.fail(str(e))


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
        models.NutrientEnergy(nutrient=nutrient_1, amount=4)

        assert amdr_recommendation.profile_amount_min(profile) == 25.0

    def test_profile_amount_max_amdr(self, profile, nutrient_1, amdr_recommendation):
        """
        IntakeRecommendation.profile_amount_max() correctly calculates
        the `amount_max` for recommendations with `dri_type` = 'AMDR'.

        5%(`amount_max`)*2000kcal(`energy_requirement`)/ energy per unit
        """
        models.NutrientEnergy(nutrient=nutrient_1, amount=4)

        assert amdr_recommendation.profile_amount_max(profile) == 25.0

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_profile_amount_min_amdr_no_energy(
        self, profile, nutrient_1, amdr_recommendation
    ):
        """
        IntakeRecommendation.profile_amount_min() returns 0 for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        assert amdr_recommendation.profile_amount_min(profile) == 0

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_profile_amount_max_amdr_no_energy(
        self, profile, nutrient_1, amdr_recommendation
    ):
        """
        IntakeRecommendation.profile_amount_max() returns 0 for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        assert amdr_recommendation.profile_amount_max(profile) == 0

    def test_profile_amount_min_amdr_no_energy_warns(
        self, profile, nutrient_1, amdr_recommendation
    ):
        """
        IntakeRecommendation.profile_amount_min() issues a warning for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        with pytest.warns(UserWarning):
            amdr_recommendation.profile_amount_min(profile)

    def test_profile_amount_max_amdr_no_energy_warns(
        self, profile, nutrient_1, amdr_recommendation
    ):
        """
        IntakeRecommendation.profile_amount_max() issues a warning for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
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

    def test_save_updates_amounts_from_db(
        self, component, ingredient_nutrient_1_1, ingredient_nutrient_1_2
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
        ingredient_nutrient.save(update_amounts=True)

        ingredient_nutrient_1_2.refresh_from_db()
        assert ingredient_nutrient_1_2.amount == 2

    def test_save_updates_amounts_created(
        self, component, ingredient_nutrient_1_1, ingredient_nutrient_1_2
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was created and saved.
        """
        ingredient_nutrient_1_1.amount = 2
        ingredient_nutrient_1_1.save(update_amounts=True)

        ingredient_nutrient_1_2.refresh_from_db()
        assert ingredient_nutrient_1_2.amount == 2

    def test_save_updates_amounts_from_db_deferred(
        self, component, ingredient_nutrient_1_1, ingredient_nutrient_1_2
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
        ingredient_nutrient.save(update_amounts=True)

        ingredient_nutrient_1_2.refresh_from_db()
        assert ingredient_nutrient_1_2.amount == 2

    def test_save_update_amounts_false(
        self, component, ingredient_nutrient_1_1, ingredient_nutrient_1_2
    ):
        """
        Updating an IngredientNutrient's amount doesn't change the
        amount value of IngredientNutrient records related to the
        `nutrient's` compound nutrients if save() was called with
        `update_amounts=False`.
        """
        ingredient_nutrient_1_1.amount = 2
        ingredient_nutrient_1_1.save(update_amounts=False)

        ingredient_nutrient_1_2.refresh_from_db()
        assert ingredient_nutrient_1_2.amount == 10
