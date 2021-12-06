from django import template

register = template.Library()


@register.inclusion_tag("components/Footer/Footer.html")
def footer(logo_url, **kwargs):
    return {**kwargs, "logo_url": logo_url}


@register.inclusion_tag("components/Footer/Social.html")
def social(**kwargs):
    return {**kwargs}
