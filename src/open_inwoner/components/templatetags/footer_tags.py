from django import template

register = template.Library()


@register.inclusion_tag("components/Footer/Footer.html")
def footer(logo_url, footer_texts, **kwargs):
    """
    Describing information

    Usage:
        {% footer logo_url=settings.logo %}

    Variables:
        + logo_url: string | the location of the logo.
        + footer_texts: dict | the dictionary with the footer texts.
    """
    return {**kwargs, "logo_url": logo_url, "footer_texts": footer_texts}


@register.inclusion_tag("components/Footer/Social.html")
def social(**kwargs):
    """
    Displaying the social links.

    Usage:
        {% social %}

    Variables:
        - primary: bool | If the primary styling should be used or not.
    """
    return {**kwargs}
