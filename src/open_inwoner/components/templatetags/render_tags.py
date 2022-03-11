from django import template

from open_inwoner.utils.ckeditor import get_rendered_content

register = template.Library()


@register.filter("ckeditor_content")
def ckeditor_content(content):
    """
    Returns rendered content from ckeditor's textarea field.

    Usage:
        {{ object.content|ckeditor_content }}

    Variables:
        + content: str | Object's content
    """
    rendered_content = get_rendered_content(content)

    return rendered_content
