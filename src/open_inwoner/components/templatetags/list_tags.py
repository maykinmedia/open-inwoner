from django import template

from .helpers import create_content_wrapper

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
    return create_content_wrapper("render_list", "components/List/List.html")(
        parser, token
    )


@register.inclusion_tag("components/List/ListItem.html")
def list_item(text, description="", href="", **kwargs):
    """
    A list item?

    Usage:
        {% list_item title=_("List item title") %}

    Variables:
        + text: string | this will be the item's title.
        - caption: string | this will be the item's caption.
        - compact: bool | Whether to use compact styling.
        - description: string | this will be the item's description.
        - active: bool | if the current list item is active or not.
        - href: url | where the item links to.
        - strong: bool | Whether to use strong text.
    """
    kwargs["text"] = text
    kwargs["description"] = kwargs.get("description", description)
    kwargs["href"] = kwargs.get("href", href)
    kwargs["strong"] = kwargs.get("strong", True)
    return kwargs
