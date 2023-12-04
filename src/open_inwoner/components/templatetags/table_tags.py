from typing import List, TypedDict

from django import template
from django.utils.translation import gettext as _

from open_inwoner.accounts.views.contactmoments import KCMDict

register = template.Library()


class TableCellConfig(TypedDict):
    text: str


class TableHeaderConfig(TypedDict):
    text: str


class TableRowConfig(TypedDict):
    headers: List[TableHeaderConfig]
    cells: List[TableCellConfig]


class TableConfig(TypedDict):
    body: List[TableRowConfig]


@register.inclusion_tag("components/table/table.html")
def table(table_config: TableConfig):
    return {"table": table_config}


@register.inclusion_tag("components/table/table.html")
def case_table(case: dict, **kwargs) -> dict:
    """
    Renders a table below the dashboard for additional values related to a Zaak (case).

    Usage:
        {% case_table case %}

    Variables:
        + case: dict | The case to be able to build the dashboard, fetching the documents and statuses of the case.

    Extra context:
        + table: TableConfig | The configuration of the table.
    """

    # build rows for data we actually have
    rows: List[TableRowConfig] = []

    def add_row_if_not_empty(key, label):
        value = case.get(key)
        if not value:
            return

        row = {"headers": [{"text": label}], "cells": [{"text": value}]}

        rows.append(row)

    add_row_if_not_empty("initiator", _("Aanvrager"))
    add_row_if_not_empty("result", _("Resultaat"))
    add_row_if_not_empty("end_date", _("Einddatum"))
    add_row_if_not_empty("end_date_planned", _("Verwachte einddatum"))
    add_row_if_not_empty("end_date_legal", _("Wettelijke termijn"))

    table_config: TableConfig = {"body": rows}

    return {
        **kwargs,
        "table": table_config,
    }


@register.inclusion_tag("components/table/table.html")
def contactmoment_table(kcm: KCMDict, **kwargs) -> dict:
    """
    Renders a table below the dashboard for additional values related to a Zaak (case).

    Usage:
        {% contactmoment_table kcm %}

    Variables:
        + kcm: KCMDict | The contactmoment to be able to build the table.

    Extra context:
        + table: TableConfig | The configuration of the table.
    """

    # build rows for data we actually have
    rows: List[TableRowConfig] = []

    def add_row_if_not_empty(key, label):
        value = kcm.get(key)
        if not value:
            return

        row = {"headers": [{"text": label}], "cells": [{"text": value}]}

        rows.append(row)

    add_row_if_not_empty("identificatie", _("Identificatie"))
    add_row_if_not_empty("type", _("Type"))
    add_row_if_not_empty("onderwerp", _("Onderwerp"))
    add_row_if_not_empty("text", _("Vraag"))
    add_row_if_not_empty("antwoord", _("Antwoord"))

    table_config: TableConfig = {"body": rows}

    return {
        **kwargs,
        "table": table_config,
    }
