from django import template

from open_inwoner.components.utils import ContentsNode, parse_component_with_args

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
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_card")
    nodelist = parser.parse(("endrender_card",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Card/RenderCard.html", **context_kwargs)
