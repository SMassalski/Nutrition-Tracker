"""General utility functions."""
import io
import os
from typing import List, Union


def weighted_dict_sum(dicts: List[dict], weights: List[float]) -> dict:
    """Calculate the per key weighted sum of dictionary values.

    In case of key mismatch, the missing value is considered equal to 0.

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
    keys = {k for key_list in keys for k in key_list}  # Flatten and turn into a set

    result = {
        key: sum(value.get(key, 0) * weights[idx] for idx, value in enumerate(dicts))
        for key in keys
    }
    return result


def open_or_pass(
    file: Union[str, os.PathLike, io.IOBase], *args, **kwargs
):  # pragma: no cover
    """Open a file if `file` is a path.

    If `file` is an instance subclassing `io.IOBase` the function
    returns the `file` unchanged.

    Parameters
    ----------
    file
        File or path to the file to be opened.
    args
        Positional arguments passed to open() if used.
    kwargs
        Keyword arguments passed to open() if used.
    Returns
    -------
    io.IOBase
        The open file.
    """
    if isinstance(file, io.IOBase):
        return file
    return open(file, *args, **kwargs)


def get_conversion_factor(from_unit: str, to_unit: str, name: str = None) -> float:
    """Get the factor needed to convert between two units.

    Parameters
    ----------
    from_unit
        Unit to be converted from.
    to_unit
        Unit to be converted to.
    name
        The name of the nutrient being converted. Required only when
        one of the units is `IU`
    Returns
    -------
    float
    """

    # skip if units are the same
    if from_unit == to_unit:
        return 1.0

    # 1 of the unit denoted by the `key` == `value` of grams
    gram_conversion_factors = {
        "UG": 1e-6,
        "MG": 0.001,
        "G": 1,
        "IU": {"Vitamin A": 0.3 * 1e-6, "Vitamin D": 0.025 * 1e-6},
    }

    # From nutrient's unit to grams
    if from_unit == "IU":
        f2g = gram_conversion_factors["IU"].get(name)
    else:
        f2g = gram_conversion_factors.get(from_unit)
    if f2g is None:
        raise ValueError(f"Unit {from_unit} was not recognized.")

    # From grams to target unit
    if to_unit == "IU":
        g2t = gram_conversion_factors["IU"].get(name)
    else:
        g2t = gram_conversion_factors.get(to_unit)
    if g2t is None:
        raise ValueError(f"Unit {to_unit} was not recognized.")

    return f2g / g2t


def pounds_to_kilograms(weight: int) -> int:
    """Convert the given weight in pounds to kilograms."""
    return round(weight * 0.454)
