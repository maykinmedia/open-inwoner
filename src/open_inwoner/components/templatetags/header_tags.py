from django import template

from open_inwoner.configurations.models import SiteConfiguration

register = template.Library()


@register.inclusion_tag("components/Header/AccessibilityHeader.html")
def accessibility_header(request, **kwargs):
    """
    This is used to display the accessibility header

    Usage:
        {% accessibility_header request=request%}

    Variables:
        + request: Request | The django request object.

    Extra context:
        - help_text: str | The help text depending on the current path.
    """
    config = SiteConfiguration.get_solo()
    kwargs["help_text"] = config.get_help_text(request)
    return {**kwargs, "request": request}
