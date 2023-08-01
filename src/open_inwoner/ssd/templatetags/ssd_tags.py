from django import template
from django.template.defaultfilters import stringfilter

import markdown as md

register = template.Library()


@register.simple_tag
def get_detail_value_for_column(detail: dict, column: str) -> str:
    """
    :returns: the detail value (amount in Euro as `str`) if the value belongs
    in `column`, empty string otherwise
    """
    if detail["column"] == column:
        return detail["value"]
    return ""


@register.filter()
@stringfilter
def markdown(value):
    return md.markdown(value, extensions=["markdown.extensions.fenced_code"])
