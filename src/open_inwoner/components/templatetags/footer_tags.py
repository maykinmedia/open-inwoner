from django import template

register = template.Library()


@register.inclusion_tag("components/Footer/Footer.html")
def footer(footer_texts, **kwargs):
    """
    Generating the entire footer.

    Usage:
        {% footer footer_texts=settings.footer_texts %}

    Variables:
        + footer_texts: dict | the dictionary with the footer texts.
    """
    return {**kwargs, "footer_texts": footer_texts}


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
