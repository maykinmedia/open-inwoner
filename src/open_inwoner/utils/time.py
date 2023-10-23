"""
Utility functions/classes related to (date-)times
"""

import datetime as dt
from typing import Sequence

from django.utils import timezone


def is_new(instance: object, attribute_name: str, delta: dt.timedelta) -> bool:
    """
    Return `True` if `instance` is "new", `False` otherwise

    An object is new iff it has an attribute named `$attribute_name`
    which has been set no earlier than some point in the past calculated
    on the basis of `delta`.
    """
    new = False

    date_time = getattr(instance, attribute_name, None)

    if not date_time:
        return False
    try:
        new = (timezone.now() - date_time) <= delta
    except TypeError:  # instance has naive datetime
        new = (dt.datetime.now() - date_time) <= delta

    return new


def has_new_elements(
    collection: Sequence, attribute_name: str, delta: dt.timedelta
) -> bool:
    """
    Return `True` if `collection` has at least one "new" element, `False`
    otherwise
    """
    return any(is_new(elem, attribute_name, delta) for elem in collection)
