from typing import TypedDict

from django import template
from django.utils.translation import gettext as _

register = template.Library()


class Metric(TypedDict):
    icon: str
    label: str
    value: str


class DashboardConfig(TypedDict):
    metrics: list[Metric]


class Row(TypedDict):
    label: str
    value: str


class TableConfig(TypedDict):
    rows: list[Row]


@register.inclusion_tag("components/Dashboard/Dashboard.html")
def case_dashboard(case: dict, **kwargs) -> dict:
    """
    Renders a dashboard for values related to a Zaak (case).

    Usage:
        {% case_dashboard case %}

    Variables:
        + case: dict | The case to be able to build the dashboard, fetching the documents and statusses of the case.

    Extra context:
        + config: DashboardConfig | The configuration of the dashboard.
    """
    config: DashboardConfig = {
        "metrics": [
            {
                "icon": "inventory_2",
                "label": _("Aanvraag"),
                "value": case.get("identification"),
            },
            {
                "icon": "calendar_today",
                "label": _("Datum"),
                "value": case.get("start_date"),
            },
            {
                "icon": "task_alt",
                "label": _("Status"),
                "value": case.get("current_status"),
            },
            {
                "icon": "description",
                "label": _("Documenten"),
                "value": len(case.get("documents")),
            },
        ]
    }

    return {
        **kwargs,
        "config": config,
    }


@register.inclusion_tag("components/Dashboard/Table.html")
def case_table(case: dict, **kwargs) -> dict:
    """
    Renders a table below the dashboard for additional values related to a Zaak (case).

    Usage:
        {% case_table case %}

    Variables:
        + case: dict | The case to be able to build the dashboard, fetching the documents and statusses of the case.

    Extra context:
        + table: TableConfig | The configuration of the table.
    """

    # build rows for data we actually have
    rows = []
    if case.get("identification"):
        rows.append(
            {
                "label": _("Aanvrager"),
                "value": case.get("initiator"),
            }
        )
    if case.get("end_date"):
        rows.append(
            {
                "label": _("Wordt afgerond"),
                "value": case.get("end_date"),
            }
        )

    table: TableConfig = {"rows": rows}

    return {
        **kwargs,
        "table": table,
    }
