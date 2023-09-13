from datetime import datetime
from typing import Optional, Union

from django.template.defaultfilters import date as django_date

from ..service.jaaropgave.fwi_include_resolved import CdPositiefNegatief


def calculate_loon_zvw(fiscalloon: int, vergoeding_premie_zvw: int) -> int:
    return fiscalloon - vergoeding_premie_zvw


def format_date_month_name(date_str) -> str:
    """
    204805 -> Mei 2048
    """
    if not date_str:
        return ""

    patched = date_str + "01"
    dt = datetime.strptime(patched, "%Y%m%d")

    formatted_date = django_date(dt, "M Y")

    return formatted_date


def format_period(date_str: Optional[str]) -> str:
    """
    20480501 -> 01-05-2048
    """
    if not date_str:
        return ""
    return datetime.strptime(date_str, "%Y%m%d").strftime("%d-%m-%Y")


def format_string(*args: Optional[Union[str, int]]) -> str:
    """
    Return a formatted string, filtering out `None` elements from `args`,
    normalizing datatypes by casting `int` to `str`, and cleaning up whitespace
    """
    filtered = filter(None, args)
    cleaned = [str(item).strip() for item in filtered]
    return " ".join(cleaned)


def get_sign(sign: CdPositiefNegatief) -> Union[CdPositiefNegatief, str]:
    return sign if sign == "-" else ""
