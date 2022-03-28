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
        + statuses: Status[] | List of Status objects.
    """
    return {**kwargs, "object_list": sorted(statuses, key=lambda s: s["date"])}


@register.inclusion_tag("components/status/status_list.html")
def case_status_list(case_statuses: StatusType) -> dict:
    """
    Shows multiple statuses in an (historic) list for a case.

    Usage:
        {% case_status_list case_statuses %}

    Variables:
        + case_statuses: StatusType[] | List of StatusType objects.
    """
    statuses = [
        {
            "icon": "check",
            "label": case_status.statustoelichting,
            "date": case_status.datum_status_gezet,
        }
        for case_status in case_statuses
    ]
    return status_list(statuses)
