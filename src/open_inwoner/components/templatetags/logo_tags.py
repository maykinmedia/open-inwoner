from django import template

register = template.Library()


@register.inclusion_tag("components/Logo/Logo.html")
def logo(src, alt, **kwargs):
    """
    Display the logo

    Usage:
        {% logo %}

    Variables:
        + src: string | the location of the logo.
        + alt: string | the alt text of the logo
        - title: string | the title of the logo
    """
    return {**kwargs, "src": src, "alt": alt}
