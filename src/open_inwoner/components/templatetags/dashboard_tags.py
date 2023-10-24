from typing import Optional, TypedDict

from django import template
from django.utils.translation import gettext as _

from open_inwoner.accounts.views.contactmoments import KCMDict

register = template.Library()


class Metric(TypedDict):
    icon: str
    label: str
    value: Optional[str]


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


@register.inclusion_tag("components/Dashboard/Dashboard.html")
def contactmoment_dashboard(kcm: KCMDict, **kwargs) -> dict:
    """
    Renders a dashboard for values related to a Zaak (case).

    Usage:
        {% contactmoment_dashboard kcm %}

    Variables:
        + kcm: KCMDict | The contactmoment to be able to build the dashboard.

    Extra context:
        + config: DashboardConfig | The configuration of the dashboard.
    """
    config: DashboardConfig = {
        "metrics": [
            {
                "icon": "calendar_today",
                "label": _("Ontvangstdatum"),
                "value": kcm.get("registered_date"),
            },
            {
                "icon": "inventory_2",
                "label": _("Contactwijze"),
                "value": kcm.get("channel"),
            },
            {
                "icon": "task_alt",
                "label": _("Status"),
                "value": kcm.get("status"),
            },
        ]
    }

    return {
        **kwargs,
        "config": config,
    }
