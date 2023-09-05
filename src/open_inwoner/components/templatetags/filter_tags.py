from django import template

register = template.Library()


@register.inclusion_tag("components/Filter/Filter.html")
def filters(field, **kwargs):
    """
    Building the filter options for the search page.

    Usage:
        {% filters field=field %}

    Variables:
        + field: Field | This is a form field.
    """
    return {**kwargs, "field": field}
