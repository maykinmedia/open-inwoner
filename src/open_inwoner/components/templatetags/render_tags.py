from django import template

import structlog

from open_inwoner.utils.html import get_rendered_content

register = template.Library()


logger = structlog.stdlib.get_logger(__name__)


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
    except (AttributeError, TypeError):
        logger.warning("Could not render content", exc_info=True)
        return ""
