from django import template

register = template.Library()


@register.inclusion_tag("components/Condition/ConditionList.html")
def condition_list(conditions, **kwargs):
    """
    Generate a list of conditions

    Usage:
        {% file_list files=Product.files.all %}
        {% file_list files=Product.files.all title="Bestanden" h1=True %}

    Variables:
        + conditions: Condition[] | conditions to render
        - negative: bool | render the checkmarks with negative color
    """
    return {**kwargs, "conditions": conditions}
