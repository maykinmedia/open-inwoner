from django import template
from django.urls import NoReverseMatch, reverse

from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.inclusion_tag("components/Action/Actions.html")
def actions(actions, **kwargs):
    """
    actions: Action[] | All the actions that will be shown
    """
    kwargs.update(actions=actions)
    return kwargs
