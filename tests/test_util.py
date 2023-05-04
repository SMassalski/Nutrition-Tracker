"""Tests of general utility functions."""
import pytest
from util import get_conversion_factor, weighted_dict_sum


def test_weighted_dict_sum_treats_missing_keys_as_zeros():
    """
    weighted_dict_sum() when adding two dictionaries with one containing
    a key that is not in the other treats the missing key's value as
    equal to zero.
    """
    first_dict = {"a": 1, "b": 1}
    second_dict = {"a": 1}
    weights = [1, 1]
    expected = {"a": 2, "b": 1}
    assert weighted_dict_sum([first_dict, second_dict], weights) == expected


def test_weighted_dict_sum_applies_weights_correctly():
    """
    weighted_dict_sum() multiplies dictionary values by their respective
    weights.
    """
    first_dict = {"a": 1, "b": 1}
    second_dict = {"a": 1, "b": 3}
    weights = [1, 5]
    expected = {"a": 6, "b": 16}
    assert weighted_dict_sum([first_dict, second_dict], weights) == expected


# get_conversion_factor() tests
@pytest.mark.parametrize(
    "units,expected",
    [
        (("UG", "UG"), 1.0),
        (("UG", "MG"), 0.001),
        (("UG", "G"), 1e-06),
        (("MG", "UG"), 1000.0),
        (("MG", "MG"), 1.0),
        (("MG", "G"), 0.001),
        (("G", "UG"), 1000000.0),
        (("G", "MG"), 1000.0),
        (("G", "G"), 1.0),
    ],
)
def test_get_conversion_factor_metric_prefixes(units, expected):
    """
    get_conversion_factor selects the correct factor for different
    metric prefixes (micro-, milli- and without).
    """
    assert get_conversion_factor(*units) == pytest.approx(expected)


@pytest.mark.parametrize(
    "units,expected",
    [
        (("IU", "UG"), 0.3),
        (("IU", "MG"), 0.0003),
        (("IU", "G"), 3e-07),
        (("UG", "IU"), 3.3333333333333335),
        (("MG", "IU"), 3333.3333333333335),
        (("G", "IU"), 3333333.3333333335),
    ],
)
def test_test_get_conversion_factor_vit_a_iu(units, expected):
    """
    get_conversion_factor selects the correct factor for vitamin A IU.
    """
    assert get_conversion_factor(*units, "Vitamin A") == pytest.approx(expected)


@pytest.mark.parametrize(
    "units,expected",
    [
        (("IU", "UG"), 0.025),
        (("IU", "MG"), 2.5e-05),
        (("IU", "G"), 2.5e-08),
        (("UG", "IU"), 40.0),
        (("MG", "IU"), 40000.0),
        (("G", "IU"), 40000000.0),
    ],
)
def test_test_get_conversion_factor_vit_d_iu(units, expected):
    """
    get_conversion_factor selects the correct factor for vitamin D IU.
    """
    assert get_conversion_factor(*units, "Vitamin D") == pytest.approx(expected)


def test_get_conversion_factor_raises_exception_on_unknown_from_unit():
    """
    get_conversion_factor raises an exception when the unit to be
    converted is unknown.
    """
    with pytest.raises(ValueError):
        assert get_conversion_factor("unknown", "IU")


def test_get_conversion_factor_raises_exception_on_unknown_target_unit():
    """
    get_conversion_factor raises an exception when the unit to be
    converted to is unknown.
    """
    with pytest.raises(ValueError):
        assert get_conversion_factor("UG", "unknown")
