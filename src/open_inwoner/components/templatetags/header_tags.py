from django import template

register = template.Library()


@register.inclusion_tag("components/Header/AccessibilityHeader.html")
def accessibility_header(configurable_text, **kwargs):
    """
    This is used to display the accessibility header

    Usage:
        {% accessibility_header configurable_text=configurable_text %}

    Variables:
        + configurable_text: dict | The dictionary that contains all the configurable texts.
    """
    return {**kwargs, "configurable_text": configurable_text}


@register.inclusion_tag("components/Header/Header.html")
def header(logo_url, categories, request, configurable_text, **kwargs):
    """
    Displaying the header.

    Usage:
        {% header logo_url=settings.logo categories=Category.objects.all request=request configurable_text=configurable_text %}

    Variables:
        + logo_url: string | The url of the logo.
        + categories: Category[] | The categories that should be displayed in the theme dropdown.
        + request: Request | the django request object.
        + configurable_text: dict | The dictionary that contains all the configurable texts.
    """
    return {
        **kwargs,
        "logo_url": logo_url,
        "categories": categories,
        "request": request,
        "configurable_text": configurable_text,
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
