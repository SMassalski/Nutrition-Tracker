import pytest
from core import models
from core.models.nutrient import NutrientTypeHierarchyError
from django.db import IntegrityError


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

    def test_update_compound_energy(self, nutrient_1, nutrient_2, component):
        nutrient_1.energy = 5
        nutrient_1.save()
        nutrient_2.energy = 10
        nutrient_2.unit = "G"
        nutrient_2.save()

        nutrient_2.update_compound_energy()

        assert nutrient_2.energy == 5

    def test_update_compound_energy_adjusts_for_different_units(
        self, nutrient_1, nutrient_2, component
    ):
        nutrient_1.energy = 5
        nutrient_1.save()
        nutrient_2.energy = 10
        nutrient_2.unit = "MG"
        nutrient_2.save()

        nutrient_2.update_compound_energy()

        assert nutrient_2.energy == 5000

    def test_component_save_updates_compound_energy(
        self, nutrient_1, nutrient_2, component
    ):
        nutrient_2.energy = 10
        nutrient_2.unit = "G"
        nutrient_2.save()

        nutrient_1.energy = 5
        nutrient_1.save()

        nutrient_2.refresh_from_db()
        assert nutrient_2.energy == 5


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

    def test_delete_updates_compound_ingredient_nutrient(
        self, ingredient_1, nutrient_1, nutrient_2, ingredient_nutrient_1_1, component
    ):
        nutrient_3 = models.Nutrient.objects.create(name="3", unit="UG")
        models.NutrientComponent.objects.create(target=nutrient_2, component=nutrient_3)
        models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient_3, amount=10
        )
        component.delete()

        instance = models.IngredientNutrient.objects.get(
            ingredient=ingredient_1, nutrient=nutrient_2
        )
        assert instance.amount == 10

    def test_delete_last_removes_compound_ingredient_nutrient(
        self, ingredient_1, nutrient_1, nutrient_2, ingredient_nutrient_1_1, component
    ):
        component.delete()

        assert not models.IngredientNutrient.objects.filter(
            ingredient=ingredient_1, nutrient=nutrient_2
        ).exists()

    def test_save_updates_compound_nutrients_energy(self, nutrient_1, nutrient_2):
        nutrient_2.energy = 4
        nutrient_2.unit = "G"
        nutrient_2.save()

        models.NutrientComponent.objects.create(target=nutrient_1, component=nutrient_2)

        assert nutrient_1.energy == 4

    def test_delete_updates_compound_nutrients_energy(
        self, nutrient_1_energy, nutrient_2, component
    ):
        nutrient_2.unit = "G"
        nutrient_2.save()
        nutrient_2.update_compound_energy()

        component.delete()

        nutrient_2.refresh_from_db()
        assert nutrient_2.energy == 0


class TestNutrientType:
    """Tests of the NutrientType model class."""

    def test_save_parent_nutrient_none(self, nutrient_1):
        """
        NutrientTypes save without raising an error
        if the `parent_nutrient` is None.
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
