from django import template
from .form_tags import parse_component_with_args
from ...utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.tag()
def render_list(parser, token):
    """
    Nested content supported.
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_list")
    nodelist = parser.parse(("endrender_list",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/List/List.html", **context_kwargs)


@register.inclusion_tag("components/List/ListItem.html")
def list_item(text, description="", href="", **kwargs):
    """
    title: string | this will be the item's title.
    description: string | this will be the item's description. (Optional)
    href: url | where the item links to. (Optional)
    """
    kwargs["text"] = text
    kwargs["description"] = kwargs.get("description", description)
    kwargs["href"] = kwargs.get("href", href)
    return kwargs
