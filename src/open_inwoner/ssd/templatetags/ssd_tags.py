from django import template
from django.template.defaultfilters import stringfilter

import markdown as md

register = template.Library()


@register.simple_tag
def format_float_repr(value: str) -> str:
    return "{:.2f}".format(float(value) / 100).replace(".", ",")


@register.simple_tag
def get_detail_value_for_column(detail, column: str) -> str:
    """
    :returns: the detail/componenthistorie value (amount in Euro as `str`)
    if the value belongs in `column`, empty string otherwise
    """
    # associate the detail's column index with column name for comparison
    column_index = detail.indicatie_kolom.value

    if column_index == "1":
        detail_column = "plus"
    elif column_index == "2":
        detail_column = "minus"
    else:
        detail_column = "base"

    if detail_column == column:
        return format_float_repr(detail.bedrag.waarde_bedrag)
    return ""


@register.filter()
@stringfilter
def markdown(value):
    return md.markdown(value, extensions=["markdown.extensions.fenced_code"])
