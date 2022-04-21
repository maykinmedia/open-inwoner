from django import template

register = template.Library()


@register.inclusion_tag("components/status/status_list.html")
def status_list(final_statuses: list[dict], **kwargs) -> dict:
    """
    Shows multiple statuses in an (historic) list.

    Usage:
        {% status_list final_statuses %}

    Variables:
        + final_statuses: list[dict] | List of dictionaries with all the necessary data for the frontend.
    """
    return {
        "final_statuses": final_statuses,
        **kwargs,
    }
