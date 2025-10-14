import logging

from django import template

from open_inwoner.utils.html import get_rendered_content

register = template.Library()


logger = logging.getLogger(__name__)


@register.filter("prosemirror_content")
def prosemirror_content(content):
    """
    Returns rendered content from ProsemirrorModelField

    Usage:
        {{ object.content|prosemirror_content }}

    Variables:
        + content: str | Object's content
    """
    if content is None:
        return ""
    try:
        return get_rendered_content(content)
    except (AttributeError, TypeError) as e:
        logger.warning("Could not render content: %s", e)
        return ""
