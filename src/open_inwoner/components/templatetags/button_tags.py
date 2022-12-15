from django import template
from django.urls import NoReverseMatch, reverse

from open_inwoner.components.utils import ContentsNode, parse_component_with_args

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
        - mobile: booleam | If the button row should only be displayed on mobile screens.

    Extra context:
        - contents: string (HTML) | this is the context between the button_row and endbutton_row tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "button_row")
    nodelist = parser.parse(("endbutton_row",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Button/ButtonRow.html", **context_kwargs)


@register.inclusion_tag("components/Button/Button.html")
def button(text, **kwargs):
    """
    Creating a button. This can be a HTML button or an anchor element.

    Usage:
        {% button text="Button" icon="arrow-forward" primary=True %}

    Variables:
        + text: string | this will be the button text.
        - class: str | Additional classes.
        - hide_text: bool | whether to hide the text and use aria attribute instead.
        - href: url or string | where the link links to (can be url name).
        - uuid: string | if href is an url name, pk for reverse can be passed.
        - size: enum[small, big] | If the button should be smaller or bigger.
        - open: bool | If the open style button should be used.
        - bordered: bool | If the border should be colored.
        - primary: bool | If the primary colors should be used.
        - secondary: bool | If the secondary colors should be used.
        - transparent: bool | If the button does not have a background or border.
        - pill: bool | Display the button as a pill.
        - disabled: bool: If the button is disabled.
        - icon: string | the icon that you want to display.
        - icon_position: enum[before, after] | where the icon should be positioned to the text.
        - icon_outlined: bool | if the outlined icons should be used.
        - type: string | the type of button that should be used.
        - title: string | The HTML title attribute if different than the text.
        - extra_classes: string | Extra classes that need to be added to the button
        - extra_attributes: dict | Extra attributes that need to be added to the button

    Extra context:
        - classes: string | all the classes that the button should have.
    """

    def get_classes():
        extra_classes = kwargs.get("extra_classes")
        classnames = "button"

        if extra_classes:
            classnames += f" {extra_classes}"

        if kwargs.get("icon"):
            if not kwargs.get("text"):
                classnames += " button--textless"
            classnames += " button--icon"

        icon_position = kwargs.get("icon_position")
        if icon_position:
            classnames += f" button--icon-{icon_position}"

        size = kwargs.get("size")
        if size:
            classnames += f" button--{size}"

        if kwargs.get("open"):
            classnames += " button--open"

        if kwargs.get("bordered"):
            classnames += " button--bordered"

        if kwargs.get("primary"):
            classnames += " button--primary"

        if kwargs.get("secondary"):
            classnames += " button--secondary"

        if kwargs.get("transparent"):
            classnames += " button--transparent"

        if kwargs.get("disabled"):
            classnames += " button--disabled"

        if kwargs.get("pill"):
            classnames += " button--pill"

        if kwargs.get("class"):
            classnames += f" {kwargs.get('class')}"

        return classnames

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

    kwargs["classes"] = get_classes()
    kwargs["text"] = text
    return {**kwargs}
