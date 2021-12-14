from django import template

register = template.Library()


@register.inclusion_tag("components/Icon/Icon.html")
def icon(icon, **kwargs):
    """
    icon: the name of the icon.
    outlined: if we need to use the outlined icon (Optional)
    """
    return {**kwargs, "icon": icon}
