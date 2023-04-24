import pytest
from main.models import IngredientNutrient, IntermediateNutrient, Nutrient
from model_util import get_conversion_factor, transfer_nutrient_data

# NOTE:
#  - RAE stands for retinol activity equivalent and is used as a
#    measure of vitamin A.
#  - DFE stands for dietary folate equivalent and is used as a
#    measure of vitamin B9 (folate).
#  - IU stands for international units. The conversion factor to mcg
#    differs between vitamins. (0.3 mcg/IU for vit A, 0.025 for vit D).
#  - Cysteine and cystine (latter being a dimer of the former) are
#    different molecules and sometimes can be conflated. (It's assumed
#    it was conflated in fdc sr_legacy dataset where only cystine is
#    listed but the mass / amount is ultimately the same).


@pytest.fixture
def generic_intermediate_nutrient(db, nutrient_2):
    """Regular (not an exception) intermediate nutrient."""
    intermediate_nutrient = IntermediateNutrient.objects.create(
        name="generic_intermediate", unit="UG"
    )
    nutrient_2.internal_nutrient = intermediate_nutrient
    nutrient_2.save()
    return intermediate_nutrient


# Vitamin A fixtures
@pytest.fixture
def intermediate_vitamin_a(db):
    """Vitamin A intermediate nutrient."""
    intermediate_nutrient = IntermediateNutrient.objects.create(
        name="Vitamin A", unit="UG"
    )
    return intermediate_nutrient


@pytest.fixture
def vitamin_a_rae(db, ingredient_1, intermediate_vitamin_a):
    """Vitamin A nutrient in RAE mcg."""
    nutrient = Nutrient.objects.create(
        name="Vitamin A, RAE", unit="UG", internal_nutrient=intermediate_vitamin_a
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )
    return nutrient


@pytest.fixture
def vitamin_a_iu(db, ingredient_1, intermediate_vitamin_a):
    """Vitamin A nutrient in IU."""
    nutrient = Nutrient.objects.create(
        name="Vitamin A, IU", unit="IU", internal_nutrient=intermediate_vitamin_a
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=2
    )
    return nutrient


# Vitamin D fixtures
@pytest.fixture
def intermediate_vitamin_d(db):
    """Vitamin D intermediate nutrient."""
    intermediate_nutrient = IntermediateNutrient.objects.create(
        name="Vitamin D", unit="UG"
    )
    return intermediate_nutrient


@pytest.fixture
def vitamin_d(db, ingredient_1, intermediate_vitamin_d):
    """Vitamin D nutrient in mcg."""
    nutrient = Nutrient.objects.create(
        name="Vitamin D (D2 + D3)", unit="UG", internal_nutrient=intermediate_vitamin_d
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=2
    )
    return nutrient


@pytest.fixture
def vitamin_d_iu(db, ingredient_1, intermediate_vitamin_d):
    """Vitamin D nutrient in IU."""
    nutrient = Nutrient.objects.create(
        name="Vitamin D (D2 + D3), International Units",
        unit="IU",
        internal_nutrient=intermediate_vitamin_d,
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=3
    )
    return nutrient


# Vitamin B9 fixtures
@pytest.fixture
def intermediate_vitamin_b9(db):
    """Vitamin B9 intermediate nutrient."""
    intermediate_nutrient = IntermediateNutrient.objects.create(
        name="Vitamin B9", unit="UG"
    )
    return intermediate_nutrient


@pytest.fixture
def vitamin_b9_total(db, ingredient_1, intermediate_vitamin_b9):
    """Vitamin B9 nutrient as total."""
    nutrient = Nutrient.objects.create(
        name="Folate, total", unit="UG", internal_nutrient=intermediate_vitamin_b9
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=3
    )
    return nutrient


@pytest.fixture
def vitamin_b9_dfe(db, ingredient_1, intermediate_vitamin_b9):
    """Vitamin B9 nutrient as DFE."""
    nutrient = Nutrient.objects.create(
        name="Folate, DFE", unit="UG", internal_nutrient=intermediate_vitamin_b9
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=4
    )
    return nutrient


# Vitamin K fixtures
@pytest.fixture
def intermediate_vitamin_k(db):
    """Vitamin K intermediate nutrient."""
    intermediate_nutrient = IntermediateNutrient.objects.create(
        name="Vitamin K", unit="UG"
    )
    return intermediate_nutrient


@pytest.fixture
def vitamin_k_m(db, ingredient_1, intermediate_vitamin_k):
    """Vitamin K nutrient for menaquinone-4."""
    nutrient = Nutrient.objects.create(
        name="Vitamin K (Menaquinone-4)",
        unit="UG",
        internal_nutrient=intermediate_vitamin_k,
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=1
    )
    return nutrient


@pytest.fixture
def vitamin_k_dhp(db, ingredient_1, intermediate_vitamin_k):
    """Vitamin K nutrient for dihydrophylloquinone."""
    nutrient = Nutrient.objects.create(
        name="Vitamin K (Dihydrophylloquinone)",
        unit="UG",
        internal_nutrient=intermediate_vitamin_k,
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=2
    )
    return nutrient


@pytest.fixture
def vitamin_k_p(db, ingredient_1, intermediate_vitamin_k):
    """Vitamin K nutrient for phylloquinone."""
    nutrient = Nutrient.objects.create(
        name="Vitamin K (phylloquinone)",
        unit="UG",
        internal_nutrient=intermediate_vitamin_k,
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=3
    )
    return nutrient


# Cysteine fixtures
@pytest.fixture
def intermediate_cysteine(db):
    """Vitamin B9 intermediate nutrient."""
    intermediate_nutrient = IntermediateNutrient.objects.create(
        name="Cysteine", unit="MG"
    )
    return intermediate_nutrient


@pytest.fixture
def cysteine(db, ingredient_1, intermediate_cysteine):
    """Vitamin B9 nutrient as total."""
    nutrient = Nutrient.objects.create(
        name="Cysteine", unit="G", internal_nutrient=intermediate_cysteine
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=4
    )
    return nutrient


@pytest.fixture
def cystine(db, ingredient_1, intermediate_cysteine):
    """Vitamin B9 nutrient as DFE."""
    nutrient = Nutrient.objects.create(
        name="Cystine", unit="G", internal_nutrient=intermediate_cysteine
    )
    IngredientNutrient.objects.create(
        ingredient=ingredient_1, nutrient=nutrient, amount=5
    )
    return nutrient


# Generic nutrient tests
def test_transfer_generic_nutrient_data(
    generic_intermediate_nutrient, ingredient_1, ingredient_nutrient_1_2
):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for nutrients that aren't
    exceptions.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(
        name="generic_intermediate"
    )
    assert intermediate.exists()
    assert intermediate.first() == generic_intermediate_nutrient


def test_transfer_generic_nutrient_data_amount(
    generic_intermediate_nutrient, ingredient_1, ingredient_nutrient_1_2
):
    """
    transfer_nutrient_data creates relations between
    intermediate nutrients and ingredients for nutrients that aren't
    exceptions with the correct amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 10  # from ingredient_nutrient_1_2 fixture


def test_transfer_generic_nutrient_with_different_unit_data(
    db, ingredient_1, ingredient_nutrient_1_1, nutrient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients with unit conversion if needed
    """
    # nutrient_1's unit is grams
    intermediate = IntermediateNutrient.objects.create(name="test_nut", unit="MG")
    nutrient_1.internal_nutrient = intermediate
    nutrient_1.save()

    transfer_nutrient_data()
    # ingredient_1_1 amount is 1.5
    assert ingredient_1.intermediateingredientnutrient_set.first().amount == 1500


# Vitamin A tests
def test_transfer_vit_a_rae_nutrient_data(vitamin_a_rae, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for vitamin A in RAE mcg.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin A")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_a_rae.internal_nutrient


def test_transfer_vit_a_rae_nutrient_data_amount(vitamin_a_rae, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin A in RAE mcg with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 1  # from vitamin_a_rae fixture


def test_transfer_vit_a_iu_nutrient_data(vitamin_a_iu, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for vitamin A in IU.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin A")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_a_iu.internal_nutrient


def test_transfer_vit_a_iu_nutrient_data_amount(vitamin_a_iu, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin A in IU with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    # from vitamin_a_iu fixture converted from vitamin A IU to mcg by
    # multiplying the amount (2) * 0.3
    assert iin.amount == 0.6


def test_transfer_both_vit_a_nutrient_data_amount(
    vitamin_a_rae, vitamin_a_iu, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin A using the mcg amount when
    nutrients in both mcg and IU is available.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 1  # from fixture


# Vitamin D tests
def test_transfer_vit_d_nutrient_data(vitamin_d, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for vitamin D in mcg.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin D")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_d.internal_nutrient


def test_transfer_vit_d_nutrient_data_amount(vitamin_d, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin D in mcg with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 2  # from fixture


def test_transfer_vit_d_iu_nutrient_data(vitamin_d_iu, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for vitamin D in IU.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin D")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_d_iu.internal_nutrient


def test_transfer_vit_d_iu_nutrient_data_amount(vitamin_d_iu, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin D in IU with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    # from vitamin_d_iu fixture (amount=3) converted from vitamin D IU
    # to mcg by multiplying * 0.025.
    assert iin.amount == pytest.approx(0.075)  # needs approx because of float error


def test_transfer_both_vit_d_nutrient_data_amount(
    vitamin_d, vitamin_d_iu, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin D using the mcg amount when
    nutrients in both mcg and IU is available.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 2  # from fixture


# Vitamin B9 tests
def test_transfer_vit_b9_total_nutrient_data(vitamin_b9_total, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for vitamin B9 as total.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin B9")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_b9_total.internal_nutrient


def test_transfer_vit_b9_total_nutrient_data_amount(vitamin_b9_total, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin B9 as total with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 3  # from fixture


def test_transfer_vit_b9_dfe_nutrient_data(vitamin_b9_dfe, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for vitamin B9 as DFE.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin B9")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_b9_dfe.internal_nutrient


def test_transfer_vit_b9_dfe_nutrient_data_amount(vitamin_b9_dfe, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin B9 as DFE with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 4  # from fixture


def test_transfer_vit_b9_both_nutrient_data_amount(
    vitamin_b9_total, vitamin_b9_dfe, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for vitamin B9 using the `total` amount
    when nutrient as both total and DFE are available.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 3  # from fixture (b9_total)


# Vitamin K tests
def test_transfer_vitamin_k_m_nutrient_data(vitamin_k_m, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for menaquinone-4.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin K")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_k_m.internal_nutrient


def test_transfer_vitamin_k_dhp_nutrient_data(vitamin_k_dhp, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for dihydrophylloquinone.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin K")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_k_dhp.internal_nutrient


def test_transfer_vitamin_k_p_nutrient_data(vitamin_k_p, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for phylloquinone.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Vitamin K")
    assert intermediate.exists()
    assert intermediate.first() == vitamin_k_p.internal_nutrient


def test_transfer_vitamin_k_m_nutrient_data_amount(vitamin_k_m, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for menaquinone-4 with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 1  # from fixture


def test_transfer_vitamin_k_dhp_nutrient_data_amount(vitamin_k_dhp, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for dihydrophylloquinone with the
    correct amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 2  # from fixture


def test_transfer_vitamin_k_p_nutrient_data_amount(vitamin_k_p, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for phylloquinone with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 3  # from fixture


def test_transfer_vitamin_k_m_and_dhp_nutrient_data_amount(
    vitamin_k_m, vitamin_k_dhp, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for menaquinone-4 and dihydrophylloquinone
    with the correct amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 3  # from fixture 1(M) + 2(DHP)


def test_transfer_vitamin_k_m_and_p_nutrient_data_amount(
    vitamin_k_m, vitamin_k_p, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for menaquinone-4 and phylloquinone
    with the correct amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 4  # from fixture 1(M) + 3(P)


def test_transfer_vitamin_k_dhp_and_p_nutrient_data_amount(
    vitamin_k_p, vitamin_k_dhp, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for dihydrophylloquinone and phylloquinone
    with the correct amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 5  # from fixture 2(DHP) + 3(P)


def test_transfer_vitamin_k_all_nutrient_data_amount(
    vitamin_k_m, vitamin_k_p, vitamin_k_dhp, ingredient_1
):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for menaquinone-4, dihydrophylloquinone
    and phylloquinone with the correct amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 6  # from fixture 1(M) + 2(DHP) + 3(P)


# Cysteine tests
def test_transfer_cysteine_nutrient_data(cysteine, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for cysteine.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Cysteine")
    assert intermediate.exists()
    assert intermediate.first() == cysteine.internal_nutrient


def test_transfer_cysteine_nutrient_data_amount(cysteine, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for cysteine with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 4000  # from fixture * 1000 from mg/g conv.


def test_transfer_cystine_nutrient_data(cystine, ingredient_1):
    """
    transfer_nutrient_data correctly creates relations between
    intermediate nutrients and ingredients for cystine.
    """
    transfer_nutrient_data()
    intermediate = ingredient_1.intermediate_nutrients.filter(name="Cysteine")
    assert intermediate.exists()
    assert intermediate.first() == cystine.internal_nutrient


def test_transfer_cystine_nutrient_data_amount(cystine, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for cystine with the correct
    amount.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 5000  # from fixture * 1000 from mg/g conv.


def test_transfer_both_cysteine_nutrient_data_amount(cystine, cysteine, ingredient_1):
    """
    transfer_nutrient_data creates relations between intermediate
    nutrients and ingredients for cysteine amount when nutrients
    as both cysteine and cystine are available.
    """
    transfer_nutrient_data()
    iin = ingredient_1.intermediateingredientnutrient_set.first()
    assert iin.amount == 4000  # from fixture * 1000 from mg/g conv.


# get_conversion_factor tests
def test_get_conversion_factor_ug_2_ug():
    """get_conversion_factor selects the correct factor for ug to mg."""
    int_nut = IntermediateNutrient(unit="UG")
    assert get_conversion_factor(Nutrient(unit="UG", internal_nutrient=int_nut)) == 1


def test_get_conversion_factor_ug_2_mg():
    """get_conversion_factor selects the correct factor for ug to mg."""
    int_nut = IntermediateNutrient(unit="MG")
    assert (
        get_conversion_factor(Nutrient(unit="UG", internal_nutrient=int_nut)) == 0.001
    )


def test_get_conversion_factor_ug_2_g():
    """get_conversion_factor selects the correct factor for ug to g."""
    int_nut = IntermediateNutrient(unit="G")
    assert get_conversion_factor(Nutrient(unit="UG", internal_nutrient=int_nut)) == 1e-6


def test_get_conversion_factor_mg_2_ug():
    """get_conversion_factor selects the correct factor for mg to ug."""
    int_nut = IntermediateNutrient(unit="UG")
    nutrient = Nutrient(unit="MG", internal_nutrient=int_nut)
    pytest.approx(get_conversion_factor(nutrient), 1000)


def test_get_conversion_factor_mg_2_mg():
    """get_conversion_factor selects the correct factor for mg to mg."""
    int_nut = IntermediateNutrient(unit="MG")
    assert get_conversion_factor(Nutrient(unit="MG", internal_nutrient=int_nut)) == 1


def test_get_conversion_factor_mg_2_g():
    """get_conversion_factor selects the correct factor for mg to g."""
    int_nut = IntermediateNutrient(unit="G")
    assert (
        get_conversion_factor(Nutrient(unit="MG", internal_nutrient=int_nut)) == 0.001
    )


def test_get_conversion_factor_g_2_ug():
    """get_conversion_factor selects the correct factor for g to ug."""
    int_nut = IntermediateNutrient(unit="UG")
    assert get_conversion_factor(Nutrient(unit="G", internal_nutrient=int_nut)) == 1e6


def test_get_conversion_factor_g_2_mg():
    """get_conversion_factor selects the correct factor for g to mg."""
    int_nut = IntermediateNutrient(unit="MG")
    assert get_conversion_factor(Nutrient(unit="G", internal_nutrient=int_nut)) == 1000


def test_get_conversion_factor_g_2_g():
    """get_conversion_factor selects the correct factor for g to g."""
    int_nut = IntermediateNutrient(unit="G")
    assert get_conversion_factor(Nutrient(unit="G", internal_nutrient=int_nut)) == 1


def test_get_conversion_factor_vit_a_iu_2_ug():
    """
    get_conversion_factor selects the correct factor for vitamin A IU
    to ug.
    """
    int_nut = IntermediateNutrient(name="Vitamin A", unit="UG")
    assert get_conversion_factor(Nutrient(unit="IU", internal_nutrient=int_nut)) == 0.3


def test_get_conversion_factor_vit_a_iu_2_mg():
    """
    get_conversion_factor selects the correct factor for vitamin A IU
    to mg.
    """
    int_nut = IntermediateNutrient(name="Vitamin A", unit="MG")
    assert get_conversion_factor(Nutrient(unit="IU", internal_nutrient=int_nut)) == 3e-4


def test_get_conversion_factor_vit_a_iu_2_g():
    """
    get_conversion_factor selects the correct factor for vitamin A IU
    to g.
    """
    int_nut = IntermediateNutrient(name="Vitamin A", unit="G")
    assert get_conversion_factor(Nutrient(unit="IU", internal_nutrient=int_nut)) == 3e-7


def test_get_conversion_factor_vit_d_iu_2_ug():
    """
    get_conversion_factor selects the correct factor for vitamin D IU
    to ug.
    """
    int_nut = IntermediateNutrient(name="Vitamin D", unit="UG")
    nutrient = Nutrient(unit="IU", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 0.025


def test_get_conversion_factor_vit_d_iu_2_mg():
    """
    get_conversion_factor selects the correct factor for vitamin D IU
    to mg.
    """
    int_nut = IntermediateNutrient(name="Vitamin D", unit="MG")
    nutrient = Nutrient(unit="IU", internal_nutrient=int_nut)
    pytest.approx(get_conversion_factor(nutrient) == 25e-6)


def test_get_conversion_factor_vit_d_iu_2_g():
    """
    get_conversion_factor selects the correct factor for vitamin D IU
    to g.
    """
    int_nut = IntermediateNutrient(name="Vitamin D", unit="G")
    nutrient = Nutrient(unit="IU", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 25e-9


def test_get_conversion_factor_ug_2_vit_a_iu():
    """
    get_conversion_factor selects the correct factor for ug to
    vitamin A IU.
    """
    int_nut = IntermediateNutrient(name="Vitamin A", unit="IU")
    nutrient = Nutrient(unit="UG", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 1 / 0.3


def test_get_conversion_factor_mg_2_vit_a_iu():
    """
    get_conversion_factor selects the correct factor for vitamin A IU
    to mg.
    """
    int_nut = IntermediateNutrient(name="Vitamin A", unit="IU")
    nutrient = Nutrient(unit="MG", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 1 / 3e-4


def test_get_conversion_factor_g_2_vit_a_iu():
    """
    get_conversion_factor selects the correct factor for vitamin A IU
    to g.
    """
    int_nut = IntermediateNutrient(name="Vitamin A", unit="IU")
    nutrient = Nutrient(unit="G", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 1 / 3e-7


def test_get_conversion_factor_ug_2_vit_d_iu():
    """
    get_conversion_factor selects the correct factor for vitamin D IU
    to ug.
    """
    int_nut = IntermediateNutrient(name="Vitamin D", unit="IU")
    nutrient = Nutrient(unit="UG", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 40


def test_get_conversion_factor_mg_2_vit_d_iu():
    """
    get_conversion_factor selects the correct factor for vitamin D IU
    to mg.
    """
    int_nut = IntermediateNutrient(name="Vitamin D", unit="IU")
    nutrient = Nutrient(unit="MG", internal_nutrient=int_nut)
    pytest.approx(get_conversion_factor(nutrient) == 4e4)


def test_get_conversion_factor_g_2_vit_d_iu():
    """
    get_conversion_factor selects the correct factor for vitamin D IU
    to g.
    """
    int_nut = IntermediateNutrient(name="Vitamin D", unit="IU")
    nutrient = Nutrient(unit="G", internal_nutrient=int_nut)
    assert get_conversion_factor(nutrient) == 4e7


def test_get_conversion_factor_raises_exception_on_unknown_from_unit():
    """
    get_conversion_factor raises an exception when the unit to be
    converted is unknown.
    """
    int_nut = IntermediateNutrient(unit="G")
    nutrient = Nutrient(unit="unknown", internal_nutrient=int_nut)
    with pytest.raises(ValueError):
        get_conversion_factor(nutrient)


def test_get_conversion_factor_raises_exception_on_unknown_target_unit():
    """
    get_conversion_factor raises an exception when the unit to be
    converted to is unknown.
    """
    int_nut = IntermediateNutrient(unit="unknown")
    nutrient = Nutrient(unit="G", internal_nutrient=int_nut)
    with pytest.raises(ValueError):
        get_conversion_factor(nutrient)
