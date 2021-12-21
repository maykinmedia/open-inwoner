from django import template

register = template.Library()


@register.inclusion_tag("components/Footer/Footer.html")
def footer(logo_url, address_content, **kwargs):
    return {**kwargs, "logo_url": logo_url, "address_content": address_content}


@register.inclusion_tag("components/Footer/Social.html")
def social(**kwargs):
    return {**kwargs}
