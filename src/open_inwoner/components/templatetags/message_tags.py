from django import template
from django.urls import NoReverseMatch, reverse

from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.inclusion_tag("components/Message/Message.html")
def message(type, inline, title, message, action, action_text, **kwargs):
    return {
        "type": type,
        "inline": inline,
        "title": title,
        "message": message,
        "action": action,
        "action_text": action_text,
        **kwargs,
    }
