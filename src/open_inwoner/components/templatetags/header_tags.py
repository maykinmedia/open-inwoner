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


@register.inclusion_tag("components/Header/Header.html")
def header(categories, request, **kwargs):
    """
    Displaying the header.

    Usage:
        {% header categories=Category.objects.all request=request %}

    Variables:
        + categories: Category[] | The categories that should be displayed in the theme dropdown.
        + request: Request | the django request object.
    """
    return {
        **kwargs,
        "categories": categories,
        "request": request,
    }


@register.inclusion_tag("components/Header/PrimaryNavigation.html")
def primary_navigation(categories, request, **kwargs):
    """
    Displaying the primary navigation

    Usage:
        {% primary_navigation categories=Category.objects.all request=request %}

    Variables:
        + categories: Category[] | The categories that should be displayed in the theme dropdown.
        + request: Request | the django request object.
    """
    return {**kwargs, "categories": categories, "request": request}
