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
                "value": case.get("description"),
            },
            {
                "icon": "calendar_today",
                "label": _("Datum"),
                "value": case.get("start_date"),
            },
            {
                "icon": "task_alt",
                "label": _("status"),
                "value": case.get("current_status"),
            },
            {
                "icon": "description",
                "label": _("documenten"),
                "value": len(case.get("documents")),
            },
        ]
    }

    return {
        **kwargs,
        "config": config,
    }
