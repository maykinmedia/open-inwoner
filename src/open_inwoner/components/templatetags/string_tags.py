from django import template
from django.template.defaultfilters import linebreaksbr
from django.utils.html import format_html

register = template.Library()


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.simple_tag
def optional_paragraph(field):
    """
    Renders the provided optional text, if it exists, or an empty string.

    Usage:
        {% optional_paragraph field=field %}

    Variables:
        + field: Field | This is the text field.
    """
    if not field:
        return ""
    return format_html('<p class="p">{field}</p>'.format(field=linebreaksbr(field)))
