from django import template

register = template.Library()


@register.inclusion_tag("components/Icon/Icon.html")
def icon(icon, **kwargs):
    """
    Displaying an icon. This can be from Material Icons or Fontawesome brands.

    Material Icons: https://fonts.google.com/icons
    Fontawesome Brands: https://fontawesome.com/v5.15/icons?d=gallery&p=2&s=brands

    Usage:
        {% icon "arrow-forward" %}

    Variables:
        + icon: string | what icon to display.
        - outlined: bool | if the outlined material icons should be used.

    Extra context:
        - social: bool | if the icon is from Fontawesome brands.
    """

    social = icon in ["facebook", "twitter", "whatsapp", "linkedin", "x-twitter"]
    return {**kwargs, "icon": icon, "social": social}
