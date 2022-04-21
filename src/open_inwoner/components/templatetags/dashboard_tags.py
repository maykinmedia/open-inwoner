from typing import TypedDict

from django import template
from django.utils.translation import gettext as _

from zgw_consumers.api_models.documenten import Document
from zgw_consumers.api_models.zaken import Zaak
from zgw_consumers.api_models.catalogi import StatusType

register = template.Library()


class Metric(TypedDict):
    icon: str
    label: str
    value: str


class DashboardConfig(TypedDict):
    metrics: list[Metric]


@register.inclusion_tag("components/Dashboard/Dashboard.html")
def dashboard(config: DashboardConfig, **kwargs) -> dict:
    """
    Shows multiple metrics with their values.

    Usage:
        {% dashboard config %}

    Variables:
        + config: DashboardConfig | Configuration object for the dashboard.
    """
    return {
        **kwargs,
        "config": config,
    }


@register.inclusion_tag("components/Dashboard/Dashboard.html")
def case_dashboard(
    case: Zaak, status: StatusType, documents: list[Document], **kwargs
) -> dict:
    """
    Renders a dashboard for values related to a Zaak (case).

    Usage:
        {% case_dashboard case %}

    Variables:
        + case: Zaak | The case to be able to build the dashbaord, fetching the documents and statusses of the case.
        + statuses: list[Status] | The statusses that are connected to the given case.
        + documents: list[Document] | The documents that are connected to the given case.

    Extra context:
        + config: DashbaordConfig | The configuration of the dashboard.
    """
    config: DashboardConfig = {
        "metrics": [
            {
                "icon": "inventory_2",
                "label": _("Zaaknummer"),
                "value": case.identificatie,
            },
            {
                "icon": "calendar_today",
                "label": _("Datum"),
                "value": case.registratiedatum,
            },
            {
                "icon": "task_alt",
                "label": _("status"),
                "value": status.omschrijving if status else None,
            },
            {"icon": "description", "label": _("documenten"), "value": len(documents)},
        ]
    }

    return {
        **kwargs,
        "case": case,
        "documents": documents,
        "status": status,
        "config": config,
    }
