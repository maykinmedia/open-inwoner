from django import template

register = template.Library()


@register.inclusion_tag("components/Header/AccessibilityHeader.html")
def accessibility_header(**kwargs):
    return {**kwargs}


@register.inclusion_tag("components/Header/Header.html")
def header(logo_url, categories, request, **kwargs):
    return {
        **kwargs,
        "logo_url": logo_url,
        "categories": categories,
        "request": request,
    }


@register.inclusion_tag("components/Header/PrimaryNavigation.html")
def primary_navigation(categories, request, **kwargs):
    return {**kwargs, "categories": categories, "request": request}
