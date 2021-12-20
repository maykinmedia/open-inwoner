from django import template

register = template.Library()


@register.inclusion_tag("components/Filter/Filter.html")
def filter(field, **kwargs):
    return {**kwargs, "field": field}
