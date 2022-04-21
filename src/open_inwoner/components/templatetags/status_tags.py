from django import template

from zgw_consumers.api_models.catalogi import StatusType

from open_inwoner.openzaak.statuses import SubStatus

register = template.Library()


@register.inclusion_tag("components/status/status_list.html")
def status_list(
    statuses_urls,
    status_types: list[StatusType],
    status_types_done: list[str],
    substatuses: list[SubStatus],
    **kwargs
) -> dict:
    """
    Shows multiple statuses in an (historic) list.

    Usage:
        {% status_list statuses_urls status_types status_types_done substatuses %}

    Variables:
        + statuses_urls: list[str] | List of Status urls.
        + status_types: list[StatusType] | List of StatusType objects.
        + status_types_done: list[str] | List of status type urls.
        + substatuses: list[SubStatus] | List of StatusType objects.
    """
    return {
        "statuses_urls": statuses_urls,
        "status_types": status_types,
        "status_types_done": status_types_done,
        "substatuses": substatuses,
        **kwargs,
    }
