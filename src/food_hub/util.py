"""General utility functions."""
import io
import os
from typing import List, Union


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


def open_or_pass(
    file: Union[str, os.PathLike, io.IOBase], *args, **kwargs
):  # pragma: no cover
    """Open a file if `file` is a path.

    If `file` is an instance of a subclass of io.IOBase the function
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
