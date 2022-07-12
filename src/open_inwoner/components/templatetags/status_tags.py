from datetime import datetime
from typing import TypedDict

from django import template

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
    """
    return {
        **kwargs,
        "statuses": statuses,
    }
