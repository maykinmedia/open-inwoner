from django import template

register = template.Library()


@register.inclusion_tag("components/Header/AccessibilityHeader.html")
def accessibility_header(**kwargs):
    """
    This is used to display the accessibility header

    Usage:
    {% accessibility_header %}
    """
    return {**kwargs}


@register.inclusion_tag("components/Header/Header.html")
def header(logo_url, categories, request, **kwargs):
    """
    Displaying the header.

    Example:
        {% header logo_url=settings.logo categories=Category.objects.all request=request %}

    Variables:
    - logo_url: string | The url of the logo.
    - categories: Category[] | The categories that should be displayed in the theme dropdown.
    - request: Request | the django request object.
    """
    return {
        **kwargs,
        "logo_url": logo_url,
        "categories": categories,
        "request": request,
    }


@register.inclusion_tag("components/Header/PrimaryNavigation.html")
def primary_navigation(categories, request, **kwargs):
    """
    Displaying the primary navigation

    Example:
        {% primary_navigation categories=Category.objects.all request=request %}

    Variables:
    - categories: Category[] | The categories that should be displayed in the theme dropdown.
    - request: Request | the django request object.
    """
    return {**kwargs, "categories": categories, "request": request}
