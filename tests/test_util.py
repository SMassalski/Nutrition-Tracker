"""Tests of general utility functions."""
from util import weighted_dict_sum


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
