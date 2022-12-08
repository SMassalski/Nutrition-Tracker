"""General utility functions."""
from typing import List


def weighted_dict_sum(dicts: List[dict], weights: List[float]) -> dict:
    """Calculate the per key weighted sum of dictionary values.

    In case of key mismatch the missing value is considered equal to 0.

    Parameters
    ----------
    dicts
        List of dictionaries to be summed.
    weights
        List of weights for each dict in `dicts`.

    Examples
    --------
    >>> weighted_dict_sum([{"a": 1}, {"a": 1, "b": 2}], [1,5])
    {"a": 6, "b": 10}
    """
    assert len(dicts) == len(weights)
    keys = [d.keys() for d in dicts]
    keys = {k for key_list in keys for k in key_list}  # Flatten and turn into set

    result = {
        key: sum(value.get(key, 0) * weights[idx] for idx, value in enumerate(dicts))
        for key in keys
    }
    return result
