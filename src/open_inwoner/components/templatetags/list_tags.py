from django import template

from open_inwoner.components.utils import ContentsNode

from .form_tags import parse_component_with_args

register = template.Library()


@register.tag()
def render_list(parser, token):
    """
    renders a list containing list items

    Usage:
        {% render_list %}
            add a list of list items here
        {% endrender_list %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_list and endrender_list tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_list")
    nodelist = parser.parse(("endrender_list",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/List/List.html", **context_kwargs)


@register.inclusion_tag("components/List/ListItem.html")
def list_item(text, description="", href="", **kwargs):
    """
    A list item?

    Usage:
        {% list_item title=_("List item title") %}

    Variables:
        + text: string | this will be the item's title.
        - description: string | this will be the item's description.
        - href: url | where the item links to.
        - active: bool | if the current list item is active or not.
    """
    kwargs["text"] = text
    kwargs["description"] = kwargs.get("description", description)
    kwargs["href"] = kwargs.get("href", href)
    return kwargs
