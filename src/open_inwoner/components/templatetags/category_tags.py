from django import template

from open_inwoner.utils.ckeditor import get_rendered_content

register = template.Library()


@register.filter("category_ckeditor_content")
def rendered_content(content):
    """
    Returns rendered content from ckeditor's textarea field specifically

    Usage:
        {{ object|rendered_content|safe }}

    Note:
        You need to mark the rendered_content as safe in order to prevent
        escaping
    """
    return get_rendered_content(content)
