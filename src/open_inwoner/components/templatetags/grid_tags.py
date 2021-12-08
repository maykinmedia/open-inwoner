from django import template
from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.tag
def render_grid(parser, token):
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_grid")
    nodelist = parser.parse(("endrender_grid",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Grid/Grid.html", **context_kwargs)


@register.tag
def render_column(parser, token):
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_grid")
    nodelist = parser.parse(("endrender_column",))
    parser.delete_first_token()

    context_kwargs["start"] = context_kwargs.get("start", 1)
    context_kwargs["span"] = context_kwargs.get("span", 12)

    return ContentsNode(nodelist, "components/Grid/Column.html", **context_kwargs)




