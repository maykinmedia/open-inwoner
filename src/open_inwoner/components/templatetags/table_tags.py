from typing import TypedDict

from django import template
from django.urls import reverse
from django.utils.translation import gettext as _

from open_inwoner.accounts.views.contactmoments import KCMDict
from open_inwoner.openzaak.api_models import Zaak

register = template.Library()


class TableCellConfig(TypedDict):
    text: str


class TableHeaderConfig(TypedDict):
    text: str


class TableRowConfig(TypedDict):
    headers: list[TableHeaderConfig]
    cells: list[TableCellConfig]


class TableConfig(TypedDict):
    body: list[TableRowConfig]


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
    rows: list[TableRowConfig] = []

    def add_row_if_not_empty(key, label):
        value = case.get(key)
        if not value:
            return

        row: TableRowConfig = {"headers": [{"text": label}], "cells": [{"text": value}]}

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
def contactmoment_table(kcm: KCMDict, zaak: Zaak | None = None, **kwargs) -> dict:
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
    rows: list[TableRowConfig] = []

    def add_row_if_not_empty(key, label):
        value = kcm.get(key)
        if not value:
            return

        row: TableRowConfig = {"headers": [{"text": label}], "cells": [{"text": value}]}

        rows.append(row)

    if zaak:
        rows.append(
            {
                "headers": [{"text": _("Zaakidentificatie")}],
                "cells": [
                    {
                        "text": zaak.identification,
                        "url": reverse(
                            "cases:case_detail", kwargs={"object_id": str(zaak.uuid)}
                        ),
                        "hyperlink_text": _("Ga naar zaak"),
                        "class": "case-detail__link",
                    }
                ],
            }
        )

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
