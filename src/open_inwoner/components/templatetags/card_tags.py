from django import template

from .helpers import create_content_wrapper

register = template.Library()


@register.tag
def render_card(parser, token):
    """
    Render in a card. Using nested elements.

    Usage:
        {% render_card %}
            <h1 class="h1">{% trans 'Welkom' %}</h1>
        {% endrender_card %}

    Variables:
        - grid: boolean | if the card should be a grid.

    Extra context:
        - contents: string (HTML) | this is the context between the render_card and endrender_card tags
    """
    return create_content_wrapper("render_card", "components/Card/RenderCard.html")(
        parser, token
    )
