from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("components/AnchorMenu/AnchorMenu.html")
def anchor_menu(anchors, desktop, **kwargs):
    """
    Renders the actions in a filterable table.

    Usage:
        {% actions actions=actions action_form=action_form %}

    Available options:
        + anchors: List [{"to": "#title", "name": "Anchor name"}] | the anchors that should be displayed.
        + desktop: Boolean | If it is rendered for the desktop or mobile.
    """
    kwargs.update(anchors=anchors)
    return kwargs
