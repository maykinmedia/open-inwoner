from typing import TypedDict

from django import template
from django.utils.translation import gettext as _

from zgw_consumers.api_models.zaken import Zaak

from open_inwoner.openzaak.statuses import (
    fetch_case_information_objects,
    fetch_status_history,
)

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
def case_dashboard(case: Zaak, **kwargs) -> dict:
    """
    Renders a dashboard for values related to a Zaak (case).

    Usage:
        {% case_dashboard case %}

    Variables:
        + case: Zaak | The case to show values for.
    """
    documents = fetch_case_information_objects(case.url)
    statuses = fetch_status_history(case.url)
    status = None

    try:
        status = statuses[0].statustoelichting
    except IndexError:
        pass

    config: DashboardConfig = {
        "metrics": [
            {
                "icon": "inventory_2",
                "label": _("Zaaknummer"),
                "value": case.identificatie.replace("ZAAK-", ""),
            },
            {
                "icon": "calendar_today",
                "label": _("Datum"),
                "value": case.registratiedatum,
            },
            {"icon": "check", "label": _("status"), "value": status},
            {"icon": "description", "label": _("documenten"), "value": len(documents)},
        ]
    }

    return {
        **kwargs,
        "case": case,
        "documents": documents,
        "config": config,
    }
