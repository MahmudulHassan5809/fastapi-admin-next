from math import ceil
from typing import Any


def ceil_filter(value: int | float) -> int:
    """
    Rounds a number up to the nearest integer.

    Args:
        value (int or float): The number to round up.

    Returns:
        int: The rounded up number.
    """
    return ceil(value)


def getattr_filter(obj: object, attr: str) -> Any:
    """
    Gets the given attribute from the given object.

    Args:
        obj (object): The object to get the attribute from.
        attr (str): The name of the attribute to get.

    Returns:
        Any: The attribute value, or None if the attribute does not exist.
    """
    return getattr(obj, attr, None)
