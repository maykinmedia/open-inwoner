from datetime import datetime
from typing import Optional, Union

from django import template
from django.template.defaultfilters import date as django_date, stringfilter

import markdown as md

from ..service.jaaropgave import Client as JaaropgaveClient
from ..service.jaaropgave.fwi_include_resolved import CdPositiefNegatief
from ..service.uitkering import Client as UitkeringClient

register = template.Library()


def format_string(*args: Optional[Union[str, int]]) -> str:
    """
    Return a formatted string, filtering out `None` elements from `args`,
    normalizing datatypes by casting `int` to `str`, and cleaning up whitespace
    """
    filtered = filter(None, args)
    cleaned = [str(item).strip() for item in filtered]
    return " ".join(cleaned)


@register.simple_tag
def calculate_loon_zvw(specificatie) -> int:
    return specificatie.fiscaalloon.waarde_bedrag - specificatie.vergoeding_premie_zvw.waarde_bedrag


@register.simple_tag
def format_date_month_name(date_str: str) -> str:
    """
    204805 -> mei 2048
    """
    if not date_str:
        return ""

    patched = date_str + "01"
    dt = datetime.strptime(patched, "%Y%m%d")

    return django_date(dt, "M Y").lower()


@register.simple_tag
def format_float(value: str) -> str:
    """
    74017 -> 740,17
    """
    if value == "":
        return "0,00"

    try:
        return "{:.2f}".format(float(value) / 100).replace(".", ",")
    except ValueError:
        # import pdb;pdb.set_trace()
        return ""


@register.simple_tag
def format_name(client: Union[JaaropgaveClient, UitkeringClient]) -> str:
    return format_string(
        client.voorletters,
        client.voorvoegsel,
        client.achternaam,
    )


@register.simple_tag
def format_period(date_str: Optional[str]) -> str:
    """
    20480501 -> 01-05-2048
    """
    if not date_str:
        return ""
    return datetime.strptime(date_str, "%Y%m%d").strftime("%d-%m-%Y")


@register.simple_tag
def format_street(client: Union[JaaropgaveClient, UitkeringClient]) -> str:
    return format_string(
        client.adres.straatnaam,
        client.adres.huisnummer,
        client.adres.huisletter,
    )


@register.simple_tag
def format_sign_value(item) -> str:
    sign = get_sign(item.cd_positief_negatief)
    value = str(item.waarde_bedrag)

    if sign:
        return f"{sign} {value}"
    return value


@register.simple_tag
def get_detail_value_for_column(detail, column: str) -> str:
    """
    :returns: the detail/componenthistorie value (amount in Euro as `str`)
    if the value belongs in `column`, empty string otherwise
    """
    # associate the detail's column index with column name for comparison
    column_index = detail.indicatie_kolom.value

    if column_index == "1":
        detail_column = "plus"
    elif column_index == "2":
        detail_column = "minus"
    else:
        detail_column = "base"

    if detail_column == column:
        return format_float(detail.bedrag.waarde_bedrag)
    return ""


def get_sign(sign: CdPositiefNegatief) -> Union[CdPositiefNegatief, str]:
    return sign if sign == "-" else ""


@register.filter()
@stringfilter
def markdown(value):
    return md.markdown(value, extensions=["markdown.extensions.fenced_code"])
