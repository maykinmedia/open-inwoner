from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.inclusion_tag("components/Typography/Link.html")
def link(href, **kwargs):
    try:
        href = reverse(href)
    except NoReverseMatch:
        pass

    kwargs["href"] = href

    return kwargs
