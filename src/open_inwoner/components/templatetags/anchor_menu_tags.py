from django import template
from django.urls import reverse

from open_inwoner.components.utils import ComponentNode

register = template.Library()


# @register.inclusion_tag("components/AnchorMenu/AnchorMenu.html")
# def anchor_menu(anchors, desktop, **kwargs):
#     """
#     Renders the actions in a filterable table.

#     Usage:
#         {% actions actions=actions action_form=action_form %}

#     Available options:
#         + anchors: List [{"to": "#title", "name": "Anchor name"}] | the anchors that should be displayed.
#         + desktop: Boolean | If it is rendered for the desktop or mobile.
#     """
#     kwargs.update(anchors=anchors, desktop=desktop)
#     return kwargs


@register.tag()
def anchor_menu(parser, token):
    """
    Renders the anchor menu.

    Usage:
        {% anchor_menu anchors=anchors desktop=True %}

        {% anchor_menu anchors=anchors desktop=True %}
        extra content outside of the anchors
        {% endanchor_menu %}

    Available options:
        + anchors: List [{"to": "#title", "name": "Anchor name"}] | the anchors that should be displayed.
        + desktop: Boolean | If it is rendered for the desktop or mobile.

    Extra context:
        - contents: string (HTML) | this is the context between the anchor_menu and endanchor_menu tags
    """

    def context_func(context, anchors, desktop, **kwargs):
        _context = context.flatten()
        kwargs.update(anchors=anchors, desktop=desktop)
        return {**_context, **kwargs}

    node = ComponentNode(
        "anchor_menu",
        "components/AnchorMenu/AnchorMenu.html",
        parser,
        token,
        context_func,
    )
    return node.render()
