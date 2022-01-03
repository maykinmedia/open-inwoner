from django import template
from django.urls import NoReverseMatch, reverse

from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.tag
def button_row(parser, token):
    """
    Creating a row of buttons. This expects buttons inside of the component.
    This is only a wrapper to make sure that the buttons are displayed correctly.

    Usage:
        {% button_row %}
            {% button text="button 1" %}
            {% button text="button 2" %}
        {% endbutton_row %}

    Variables:
        - align: enum[right] | if the buttons should be aligned left (no align should be given) or alinged right side.

    Extra context:
        - contents: string (HTML) | this is the context between the button_row and endbutton_row tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "button_row")
    nodelist = parser.parse(("endbutton_row",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Button/ButtonRow.html", **context_kwargs)


@register.inclusion_tag("components/Button/Button.html")
def button(**kwargs):
    """
    Creating a button. This can be a HTML button or an anchor element.

    Usage:
    {% button text="Button" icon="arrow-forward" primary=True %}

    Variables:
    - text: string | this will be the button text. (Optional)
    - hide_text: bool | whether to hide the text and use aria attribute instead. (Optional).
    - href: url or string | where the link links to (can be url name). (Optional)
    - object_id: str | if href is an url name, object_id for reverse can be passed (Optional).
    - uuid: string | if href is an url name, pk for reverse can be passed (Optional).
    - size: enum[big] | If the button should be bigger. (Optional)
    - open: bool | If the open style button should be used. (Optional)
    - bordered: bool | If the border should be colored. (Optional)
    - primary: bool | If the primary colors should be used. (Optional)
    - secondary: bool | If the secondary colors should be used. (Optional)
    - transparent: bool | If the button does not have a background or border. (Optional)
    - icon: string | the icon that you want to display. (Optional)
    - icon_position: enum[before, after] | where the icon should be positioned to the text. (Optional)
    - icon_outlined: bool | if the outlined icons should be used. (Optional)
    - type: string | the type of button that should be used. (Optional)
    """
    if "text" not in kwargs and "icon" not in kwargs:
        assert False, "Either text or icon should be given"

    if "href" in kwargs:
        try:
            uuid = kwargs.get("uuid")
            object_id = kwargs.get("object_id")
            reverse_kwargs = {}
            if uuid:
                reverse_kwargs.update(uuid=uuid)
            if object_id:
                reverse_kwargs.update(object_id=object_id)
            kwargs["href"] = reverse(kwargs.get("href"), kwargs=reverse_kwargs)
        except NoReverseMatch:
            pass

    return {**kwargs}
