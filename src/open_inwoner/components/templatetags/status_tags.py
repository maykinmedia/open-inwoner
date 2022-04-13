from datetime import datetime
from typing import TypedDict

from django import template

from zgw_consumers.api_models.catalogi import StatusType

register = template.Library()


class Status(TypedDict):
    icon: str
    label: str
    date: datetime


@register.inclusion_tag("components/status/status_list.html")
def status_list(statuses: list[Status], **kwargs) -> dict:
    """
    Shows multiple statuses in an (historic) list.

    Usage:
        {% status_list statuses %}

    Variables:
        + statuses: list[Status] | List of Status objects.

    Extra context:
        + object_list: list[Status] | The statusses sorted by date.
    """
    return {
        **kwargs,
        "statuses": statuses,
        "object_list": sorted(statuses, key=lambda s: s["date"]),
    }


@register.inclusion_tag("components/status/status_list.html")
def case_status_list(case_statuses: StatusType, **kwargs) -> dict:
    """
    Shows multiple statuses in an (historic) list for a case.

    Usage:
        {% case_status_list case_statuses %}

    Variables:
        + case_statuses: list[StatusType] | List of StatusType objects to grab the statusses.

    Extra context:
        + object_list: list[Status] | The statusses sorted by date.
    """
    statuses = [
        {
            "icon": "check",
            "label": case_status.statustoelichting,
            "date": case_status.datum_status_gezet,
        }
        for case_status in case_statuses
    ]
    return {
        **kwargs,
        "case_statuses": case_statuses,
        "object_list": sorted(statuses, key=lambda s: s["date"]),
    }
