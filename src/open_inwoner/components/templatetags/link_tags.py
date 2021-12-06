from django import template

register = template.Library()


@register.inclusion_tag("components/Typography/Link.html")
def link(href, **kwargs):
    return {**kwargs, "href": href}
