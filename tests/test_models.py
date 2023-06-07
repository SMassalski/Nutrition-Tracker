"""Tests of ORM models"""
from datetime import datetime

import pytest
from django.db import IntegrityError
from main import models

# noinspection PyProtectedMember
from main.models.foods import update_compound_nutrients


@pytest.fixture()
def ingredient_1_macronutrients(db, ingredient_1):
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


# Ingredient model
def test_ingredient_string_representation():
    """Ingredient model's string representation is its name"""
    ingredient = models.Ingredient(dataset="test_dataset", name="test_name")
    assert str(ingredient) == ingredient.name


def test_ingredient_nutritional_value_returns_nutrient_amounts(
    db, ingredient_1, ingredient_nutrient_1_1, ingredient_nutrient_1_2
):
    """
    Ingredient.nutritional_value() returns a mapping of nutrients in the ingredient
    to their amounts in the ingredient.
    """
    result = ingredient_1.nutritional_value()
    assert result[ingredient_nutrient_1_1.nutrient] == ingredient_nutrient_1_1.amount
    assert result[ingredient_nutrient_1_2.nutrient] == ingredient_nutrient_1_2.amount


def test_ingredient_macronutrient_calories_returns_only_3_macronutrients(
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
    ingredient_1_macronutrients,
):
    """
    Ingredient.macronutrient_calories calculates return dict is sorted
    by keys.
    """
    assert ingredient_1_macronutrients == dict(
        sorted(ingredient_1_macronutrients.items())
    )


# Nutrient model
def test_nutrient_string_representation():
    """
    Nutrient model's string representation follows the format
    <name> (<pretty unit symbol>).
    """
    nutrient = models.Nutrient(name="test_name", unit="UG")
    assert (
        str(nutrient)
        == f"{nutrient.name} ({models.Nutrient.PRETTY_UNITS[nutrient.unit]})"
    )


def test_save_updates_amounts_from_db(db, ingredient_1):
    """
    Updating a nutrient's unit changes the amount value of related
    IngredientNutrient records so that the actual amount remains
    unchanged. Test for when the instance was loaded from the database.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient = models.Nutrient.objects.get(pk=nutrient.id)
    nutrient.unit = "MG"
    nutrient.save(update_amounts=True)

    ing_nut.refresh_from_db()

    assert ing_nut.amount == 1000


def test_save_updates_amounts_created(db, ingredient_1):
    """
    Updating a nutrient's unit changes the amount value of related
    IngredientNutrient records so that the actual amount remains
    unchanged. Test for when the instance was created and saved.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient.unit = "MG"
    nutrient.save(update_amounts=True)

    ing_nut.refresh_from_db()

    assert ing_nut.amount == 1000


def test_save_updates_amounts_from_db_deferred(db, ingredient_1):
    """
    Updating a nutrient's unit changes the amount value of related
    IngredientNutrient records so that the actual amount remains
    unchanged. Test for when the instance was loaded from the database,
    but the unit field was deferred.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient = models.Nutrient.objects.defer("unit").get(id=nutrient.id)
    nutrient.unit = "MG"
    nutrient.save(update_amounts=True)

    ing_nut.refresh_from_db()

    assert ing_nut.amount == 1000


def test_save_update_amounts_false(db, ingredient_1):
    """
    Updating a nutrient's unit doesn't change the amount value of related
    IngredientNutrient records if save was called with `update_amounts`
    set to False.
    """
    nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
    ing_nut = models.IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )

    nutrient.unit = "MG"
    nutrient.save(update_amounts=False)

    assert ing_nut.amount == 1


def test_save_updates_recommendation_amounts(db, nutrient_1):
    """
    Updating a nutrient's unit changes the amount values of related
    IntakeRecommendations records so that the actual amounts remain
    unchanged.
    """
    # nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
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


def test_save_update_amount_recommendation_none_amounts(db, nutrient_1):
    """
    Updating a nutrient's unit changes the amount values of related
    IntakeRecommendations records so that the actual amounts remain
    unchanged.
    """
    # nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
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


def test_nutrient_energy_per_unit():
    """
    Nutrient.energy_per_unit() returns the amount value of the
    nutrient's related NutrientEnergy record.
    """
    nutrient = models.Nutrient()
    models.NutrientEnergy(nutrient=nutrient, amount=5)
    assert nutrient.energy_per_unit == 5


def test_nutrient_energy_per_unit_no_energy():
    """
    Nutrient.energy_per_unit() returns 0 if the nutrient doesn't have
    a related NutrientEnergy record.
    """
    assert models.Nutrient().energy_per_unit == 0


@pytest.mark.parametrize(
    "unit,expected", [("UG", "µg"), ("MG", "mg"), ("G", "g"), ("KCAL", "kcal")]
)
def test_nutrient_pretty_unit_property(unit, expected):
    """
    Nutrient.pretty_unit property returns the nutrient's unit's symbol.
    """
    assert models.Nutrient(unit=unit).pretty_unit == expected


def test_nutrient_is_compound(db, nutrient_1, nutrient_2):
    """
    Nutrient's is_component property indicates whether the nutrient
    consists of one or more component nutrients.
    """
    nutrient_1.components.add(nutrient_2)
    assert nutrient_2.is_compound is False
    assert nutrient_1.is_compound is True


def test_nutrient_is_component(db, nutrient_1, nutrient_2):
    """
    Nutrient's is_component property indicates whether the nutrient
    is a component of a compound nutrient.
    """
    nutrient_1.components.add(nutrient_2)
    assert nutrient_1.is_component is False
    assert nutrient_2.is_component is True


class TestNutrientComponent:
    """Tests of NutrientComponents."""

    def test_nutrient_component_unique_constraint(self, db, nutrient_1, nutrient_2):
        """
        NutrientComponent has a unique together constraint for the
        target and component fields.
        """
        models.NutrientComponent.objects.create(target=nutrient_1, component=nutrient_2)
        with pytest.raises(IntegrityError):
            models.NutrientComponent.objects.create(
                target=nutrient_1, component=nutrient_2
            )

    def test_nutrient_component_self_relation_constraint(self, db, nutrient_1):
        """
        NutrientComponent cannot have the same nutrient as a target and
        as a component.
        """
        with pytest.raises(IntegrityError):
            models.NutrientComponent.objects.create(
                target=nutrient_1, component=nutrient_1
            )

    def test_nutrient_component_save_updates_compound(
        self, db, ingredient_1, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        NutrientComponent's save() method updates the `target`
        ingredient nutrient amounts.
        """
        nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")

        models.NutrientComponent.objects.create(target=nutrient, component=nutrient_1)

        ing_nut = nutrient.ingredientnutrient_set.get(ingredient=ingredient_1)

        assert ing_nut.amount == 1.5


# Meal Component model
def test_meal_component_string_representation():
    """MealComponent model's string representation is its name"""
    assert (
        str(models.MealComponent(name="test_meal_component")) == "test_meal_component"
    )


def test_meal_component_nutritional_value_calculates_nutrients(
    db, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, meal_component
):
    """
    MealComponent.nutritional_value() calculates the amount of
    each nutrient in 100g of a component.
    """
    # INFO
    # 10g of nutrient_2 in 100g of ingredient_1
    # 10g of nutrient_2 in 100g of ingredient_2

    assert meal_component.nutritional_value()[nutrient_2] == 10


def test_meal_component_nutritional_value_is_correct_with_different_final_weight(
    db, ingredient_nutrient_1_2, ingredient_nutrient_2_2, nutrient_2, meal_component
):
    """
    MealComponent.nutritional_value() calculates the amount of
    each nutrient in 100g of a component when the final weight of the
    component is not equal to the sum of the ingredient weight.
    """
    # INFO
    # 10g of nutrient_2 in 100g of ingredient_1
    # 10g of nutrient_2 in 100g of ingredient_2

    meal_component.final_weight = 50
    assert meal_component.nutritional_value()[nutrient_2] == 40


# Meal Component Ingredient model
def test_meal_component_ingredient_string_representation():
    """
    MealComponentIngredient model's string representation is the name of
    the component and the ingredient.
    """
    ingredient = models.Ingredient(name="test_ingredient")
    component = models.MealComponent(name="test_component")
    meal_component_ingredient = models.MealComponentIngredient(
        ingredient=ingredient, meal_component=component
    )
    assert str(meal_component_ingredient) == "test_component - test_ingredient"


# Meal model
def test_meal_string_representation():
    """
    Meal model's string representation is its name and formatted date.
    """
    meal = models.Meal(
        name="test_meal", date=datetime(day=1, month=1, year=2000, hour=12, minute=0)
    )
    assert str(meal) == "test_meal (12:00 - 01 Jan 2000)"


def test_meal_nutritional_value_calculates_nutrients(
    db,
    ingredient_nutrient_1_1,
    ingredient_nutrient_1_2,
    ingredient_nutrient_2_2,
    nutrient_1,
    nutrient_2,
    meal_component,
    user,
):
    """
    Meal.nutritional_value() calculates the amount of each nutrient in
    the meal.
    """
    # INFO
    # 0.75g of nutrient_1 in 100g of meal_component
    # 10g of nutrient_2 in 100g of meal_component

    # 20g of nutrient_1 in 100g of meal_component_2
    meal_component_2 = models.MealComponent.objects.create(
        name="test_component_2", final_weight=100
    )
    ingredient_3 = models.Ingredient(
        name="test_ingredient_3", external_id=111, dataset="dataset"
    )
    ingredient_3.save()
    ingredient_3.ingredientnutrient_set.create(nutrient=nutrient_1, amount=20)
    meal_component_2.ingredients.create(ingredient=ingredient_3, amount=100)
    meal = models.Meal.objects.create(user=user, name="test_meal")

    # 100g each of meal_component and meal_component_2
    meal.components.create(component=meal_component, amount=100)
    meal.components.create(component=meal_component_2, amount=100)

    result = meal.nutritional_value()
    assert result[nutrient_1] == 20.75
    assert result[nutrient_2] == 10


# Profile model tests
# The initialism EER refers to "estimated energy requirement"


def test_profile_string_representation(db):
    """
    Profile model's string representation follows the format of
    `<associated user's username>'s profile`.
    """
    user = models.User.objects.create_user(username="profile_test_user")
    profile = models.Profile(user=user)

    assert str(profile) == "profile_test_user's profile"


def test_profile_energy_calculation_for_a_man():
    """
    Profile's calculate energy method correctly calculates the EER of
    an adult male.
    """
    profile = models.Profile(
        age=35, weight=80, height=180, sex="M", activity_level="LA"
    )
    assert profile.calculate_energy() == 2819


def test_profile_energy_calculation_for_a_woman():
    """
    Profile's calculate energy method correctly calculates the EER of
    an adult female.
    """
    profile = models.Profile(age=35, weight=60, height=170, sex="F", activity_level="A")
    assert profile.calculate_energy() == 2393


def test_profile_energy_calculation_for_a_boy():
    """
    Profile's calculate energy method correctly calculates the EER of
    a non-adult male.
    """
    profile = models.Profile(age=15, weight=50, height=170, sex="M", activity_level="S")
    assert profile.calculate_energy() == 2055


def test_profile_energy_calculation_for_a_girl():
    """
    Profile's calculate energy method correctly calculates the EER of
    a non-adult female.
    """
    profile = models.Profile(age=6, weight=35, height=140, sex="F", activity_level="A")
    assert profile.calculate_energy() == 2142


def test_profile_energy_calculation_for_a_2_yo():
    """
    Profile's calculate energy method correctly calculates the EER of
    a 2-year-old child.
    """
    profile = models.Profile(age=2, weight=12, height=140, sex="F", activity_level="A")
    assert profile.calculate_energy() == 988


def test_profile_energy_calculation_for_a_lt_1_yo():
    """
    Profile's calculate energy method correctly calculates the EER of
    a 1-year-old child.
    """
    profile = models.Profile(age=0, weight=9, height=140, sex="F", activity_level="A")
    assert profile.calculate_energy() == 723


def test_profile_create_calculates_energy(db, user):
    """Saving a new profile record automatically calculates the EER."""
    profile = models.Profile(
        age=35, weight=80, height=180, sex="M", activity_level="LA", user=user
    )
    profile.save()
    profile.refresh_from_db()
    assert profile.energy_requirement == 2819


def test_profile_update_calculates_energy(db, user):
    """Updating a profile record automatically calculates the EER."""
    profile = models.Profile(
        age=35, weight=80, height=180, sex="M", activity_level="LA", user=user
    )
    profile.save()
    profile.weight = 70
    profile.save()
    profile.refresh_from_db()
    assert profile.energy_requirement == 2643


def test_food_data_source_string_representation():
    """
    The string representation of a FoodDataSource instance is its name.
    """
    assert str(models.FoodDataSource(name="test_name")) == "test_name"


# Nutrient Recommendation tests
class TestIntakeRecommendation:
    """Tests of the IntakeRecommendation model."""

    def test_recommendation_manger_for_profile_by_sex(self, db, nutrient_1):
        """
        RecommendationQuerySet.for_profile() correctly selects
        IntakeRecommendations matching a profile based on sex.
        """
        profile = models.Profile(sex="F", age=50)

        recommends = models.IntakeRecommendation.objects.bulk_create(
            [
                models.IntakeRecommendation(
                    nutrient=nutrient_1,
                    dri_type="UL",
                    sex="B",
                    age_min=18,
                    age_max=60,
                    amount_min=0,
                    amount_max=10,
                ),
                models.IntakeRecommendation(
                    nutrient=nutrient_1,
                    dri_type="RDA",
                    sex="F",
                    age_min=18,
                    age_max=60,
                    amount_min=3,
                    amount_max=10,
                ),
                models.IntakeRecommendation(
                    nutrient=nutrient_1,
                    dri_type="UL",
                    sex="M",
                    age_min=18,
                    age_max=60,
                    amount_min=0,
                    amount_max=10,
                ),
            ]
        )

        for_profile = models.IntakeRecommendation.objects.for_profile(profile)
        assert for_profile.count() == 2
        assert recommends[2] not in for_profile

    def test_recommendation_manger_for_profile_by_age(self, db, nutrient_1):
        """
        RecommendationQuerySet.for_profile() correctly selects
        IntakeRecommendations matching a profile based on age.
        """
        profile = models.Profile(sex="M", age=50)

        recommends = models.IntakeRecommendation.objects.bulk_create(
            [
                models.IntakeRecommendation(
                    nutrient=nutrient_1,
                    dri_type="UL",
                    sex="M",
                    age_min=18,
                    age_max=50,
                    amount_min=0,
                    amount_max=10,
                ),
                models.IntakeRecommendation(
                    nutrient=nutrient_1,
                    dri_type="RDA",
                    sex="M",
                    age_min=50,
                    age_max=60,
                    amount_min=3,
                    amount_max=10,
                ),
                models.IntakeRecommendation(
                    nutrient=nutrient_1,
                    dri_type="RDA",
                    sex="M",
                    age_min=20,
                    age_max=30,
                    amount_min=3,
                    amount_max=10,
                ),
            ]
        )

        for_profile = models.IntakeRecommendation.objects.for_profile(profile)
        assert for_profile.count() == 2
        assert recommends[2] not in for_profile

    def test_recommendation_manger_for_profile_age_max_is_none(self, db, nutrient_1):
        """
        RecommendationQuerySet.for_profile() treats recommendations with
        `age_max=None` as a recommendation without an upper age
        limit.
        """
        profile = models.Profile(sex="M", age=999)
        rec = models.IntakeRecommendation(
            nutrient=nutrient_1,
            dri_type="UL",
            sex="M",
            age_min=18,
            age_max=None,
            amount_min=0,
            amount_max=10,
        )
        rec.save()

        for_profile = models.IntakeRecommendation.objects.for_profile(profile)
        assert for_profile.first() == rec

    def test_recommendation_str(self):
        """
        IntakeRecommendation's string representation follows the format
        <nutrient_name> : <age_range> [<sex>] (<dri_type>).
        """
        nutrient = models.Nutrient(name="test_name")
        recommendation = models.IntakeRecommendation(
            nutrient=nutrient,
            dri_type="UL",
            sex="M",
            age_min=18,
            age_max=50,
        )

        assert str(recommendation) == "test_name : 18 - 50 [M] (UL)"

    @pytest.mark.parametrize(
        "dri_type,expected",
        [
            (models.IntakeRecommendation.AIK, 10.0),
            (models.IntakeRecommendation.AIKG, 400.0),
            (models.IntakeRecommendation.RDAKG, 400.0),
        ],
    )
    def test_recommendation_profile_amount_min(self, dri_type, expected):
        """
        IntakeRecommendation.profile_amount_min() returns the
        recommendation's `amount_min` according to it's `dri_type` and
        the set profile attributes.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_min=5.0)
        profile = models.Profile(weight=80, energy_requirement=2000)

        assert recommendation.profile_amount_min(profile) == expected

    @pytest.mark.parametrize(
        "dri_type,expected",
        [
            (models.IntakeRecommendation.AIK, 10.0),
            (models.IntakeRecommendation.AIKG, 400.0),
            (models.IntakeRecommendation.RDAKG, 400.0),
        ],
    )
    def test_recommendation_profile_amount_max(self, dri_type, expected):
        """
        IntakeRecommendation.profile_amount_max() returns the
        recommendation's `amount_max` according to it's `dri_type` and
        the set profile attributes.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_max=5.0)
        profile = models.Profile(weight=80, energy_requirement=2000)

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
    def test_recommendation_profile_amount_min_independent_type(self, dri_type):
        """
        IntakeRecommendation.profile_amount_min() returns the
        recommendation's `amount_min` unchanged if it's `dri_type`
        is independent of profile attributes.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_min=5.0)
        profile = models.Profile(weight=80, energy_requirement=2000)

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
    def test_recommendation_profile_amount_max_independent_type(self, dri_type):
        """
        IntakeRecommendation.profile_amount_max() returns the
        recommendation's `amount_max` unchanged if it's `dri_type`
        is independent of profile attributes.
        """
        recommendation = models.IntakeRecommendation(dri_type=dri_type, amount_max=5.0)
        profile = models.Profile(weight=80, energy_requirement=2000)

        assert recommendation.profile_amount_max(profile) == 5.0

    def test_recommendation_profile_amount_min_amdr(self):
        """
        IntakeRecommendation.profile_amount_min() correctly calculates
        the `amount_min` for recommendations with `dri_type` = 'AMDR'.
        """
        nutrient = models.Nutrient()
        models.NutrientEnergy(nutrient=nutrient, amount=4)
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR", amount_min=5.0, nutrient=nutrient
        )
        profile = models.Profile(energy_requirement=2000)

        assert recommendation.profile_amount_min(profile) == 25.0

    def test_recommendation_profile_amount_max_amdr(self):
        """
        IntakeRecommendation.profile_amount_max() correctly calculates
        the `amount_max` for recommendations with `dri_type` = 'AMDR'.
        """
        nutrient = models.Nutrient()
        models.NutrientEnergy(nutrient=nutrient, amount=4)
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR", amount_max=5.0, nutrient=nutrient
        )
        profile = models.Profile(energy_requirement=2000)

        assert recommendation.profile_amount_max(profile) == 25.0

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_recommendation_profile_amount_min_amdr_no_energy(self):
        """
        IntakeRecommendation.profile_amount_min() returns 0 for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        nutrient = models.Nutrient()
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR", amount_min=5.0, nutrient=nutrient
        )
        profile = models.Profile(energy_requirement=2000)

        assert recommendation.profile_amount_min(profile) == 0

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_recommendation_profile_amount_max_amdr_no_energy(self):
        """
        IntakeRecommendation.profile_amount_max() returns 0 for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        nutrient = models.Nutrient()
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR", amount_max=5.0, nutrient=nutrient
        )
        profile = models.Profile(energy_requirement=2000)

        assert recommendation.profile_amount_max(profile) == 0

    def test_recommendation_profile_amount_min_amdr_no_energy_warns(self):
        """
        IntakeRecommendation.profile_amount_min() issues a warning for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        nutrient = models.Nutrient()
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR", amount_min=5.0, nutrient=nutrient
        )
        profile = models.Profile(energy_requirement=2000)

        with pytest.warns(UserWarning):
            recommendation.profile_amount_min(profile)

    def test_recommendation_profile_amount_max_amdr_no_energy_warns(self):
        """
        IntakeRecommendation.profile_amount_max() issues a warning for
        recommendations with `dri_type` = 'AMDR' when no NutrientEnergy
        record for the related nutrient exists.
        """
        nutrient = models.Nutrient()
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR", amount_max=5.0, nutrient=nutrient
        )
        profile = models.Profile(energy_requirement=2000)

        with pytest.warns(UserWarning):
            recommendation.profile_amount_max(profile)

    def test_recommendation_profile_amount_min_none(self):
        """
        IntakeRecommendation.profile_amount_min() correctly calculates
        the `amount_min` for recommendations with `dri_type` = 'AMDR'.
        """
        recommendation = models.IntakeRecommendation(
            dri_type="AIK",
            amount_min=None,
        )
        profile = models.Profile()

        assert recommendation.profile_amount_min(profile) is None

    def test_recommendation_profile_amount_max_none(self):
        """
        IntakeRecommendation.profile_amount_max() correctly calculates
        the `amount_max` for recommendations with `dri_type` = 'AMDR'.
        """
        recommendation = models.IntakeRecommendation(
            dri_type="AMDR",
            amount_max=None,
        )
        profile = models.Profile()

        assert recommendation.profile_amount_max(profile) is None

    def test_recommendation_unique_together_constraint_null_age_max(
        self, db, nutrient_1
    ):
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


class TestUpdateCompoundNutrient:
    """Tests of the update_compound_nutrients() function."""

    def test_update_compound_nutrients(self, db, compound_nutrient):
        """
        update_compound_nutrients() updates the amounts of
        IngredientNutrients related to a compound nutrient based on the
        amounts of IngredientNutrients related to it's component nutrients.
        """
        expected = 3  # component amounts are 1 and 2

        update_compound_nutrients(compound_nutrient)

        assert compound_nutrient.ingredientnutrient_set.first().amount == expected

    def test_update_compound_nutrients_commit_false(self, db, compound_nutrient):
        """
        update_compound_nutrients() call with `commits=False` doesn't
        save updated IngredientNutrient records.
        """
        update_compound_nutrients(compound_nutrient, commit=False)

        assert not compound_nutrient.ingredientnutrient_set.exists()


class TestIngredientNutrient:
    """Tests of the IngredientNutrient model."""

    def test_save_updates_amounts_from_db(
        self, db, ingredient_1, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was loaded from the database.
        """
        nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
        ing_nut = models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient, amount=1.5
        )
        models.NutrientComponent.objects.create(target=nutrient, component=nutrient_1)

        ingredient_nutrient = models.IngredientNutrient.objects.get(
            pk=ingredient_nutrient_1_1.pk
        )
        ingredient_nutrient.amount = 2
        ingredient_nutrient.save(update_amounts=True)

        ing_nut.refresh_from_db()

        assert ing_nut.amount == 2

    def test_save_updates_amounts_created(
        self, db, ingredient_1, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was created and saved.
        """
        nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
        ing_nut = models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient, amount=1.5
        )
        models.NutrientComponent.objects.create(target=nutrient, component=nutrient_1)

        ingredient_nutrient_1_1.amount = 2
        ingredient_nutrient_1_1.save(update_amounts=True)

        ing_nut.refresh_from_db()

        assert ing_nut.amount == 2

    def test_save_updates_amounts_from_db_deferred(
        self, db, ingredient_1, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        Updating an IngredientNutrient's amount changes the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients.
        Test for when the instance was loaded from the database,
        but the amount field was deferred.
        """
        nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
        ing_nut = models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient, amount=1.5
        )
        models.NutrientComponent.objects.create(target=nutrient, component=nutrient_1)

        ingredient_nutrient = models.IngredientNutrient.objects.defer("amount").get(
            pk=ingredient_nutrient_1_1.pk
        )
        ingredient_nutrient.amount = 2
        ingredient_nutrient.save(update_amounts=True)

        ing_nut.refresh_from_db()

        assert ing_nut.amount == 2

    def test_save_update_amounts_false(
        self, db, ingredient_1, nutrient_1, ingredient_nutrient_1_1
    ):
        """
        Updating an IngredientNutrient's amount doesn't change the amount value
        of IngredientNutrient records related to the `nutrient's`
        compound nutrients if save() was called with
        `update_amounts=False`.
        """
        nutrient = models.Nutrient.objects.create(name="save_test_nutrient", unit="G")
        ing_nut = models.IngredientNutrient.objects.create(
            ingredient=ingredient_1, nutrient=nutrient, amount=1.5
        )
        models.NutrientComponent.objects.create(target=nutrient, component=nutrient_1)

        ingredient_nutrient_1_1.amount = 2
        ingredient_nutrient_1_1.save(update_amounts=False)

        ing_nut.refresh_from_db()

        assert ing_nut.amount == 1.5
