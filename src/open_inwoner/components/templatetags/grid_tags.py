from django import template

from open_inwoner.components.utils import ContentsNode, parse_component_with_args

from .helpers import create_content_wrapper

register = template.Library()


@register.tag
def render_grid(parser, token):
    """
    This is used to render in a grid.

    Usage:
    {% render_grid %}
        <div>Some content here</div>
        <div>Some content here too</div>
    {% endrender_grid %}

    Variables:
        - compact: bool | Whether to use compact mode (no gutters).

    Extra context:
        - contents: string (HTML) | this is the context between the render_grid and endrender_grid tags
    """
    return create_content_wrapper("render_grid", "components/Grid/Grid.html")(
        parser, token
    )


@register.tag
def render_column(parser, token):
    """
    Create a column on the page with content inside.

    Usage:
        {% render_column start=1 span=12 %}
            contents of the column
        {% endrender_column %}

    Variables:
        - compact: bool | Whether to use compact mode (no gutters).
        - start: (int|string) | column to start from, set to auto for standard flow.
        - span: int | column span. Max is 12 columns
        - extra_classes: string | Extra classes for the column

    Extra context:
        - contents: string (HTML) | this is the context between the render_column and endrender_column tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_grid")
    nodelist = parser.parse(("endrender_column",))
    parser.delete_first_token()

    context_kwargs["start"] = context_kwargs.get("start", 1)
    context_kwargs["span"] = context_kwargs.get("span", 12)

    return ContentsNode(nodelist, "components/Grid/Column.html", **context_kwargs)
