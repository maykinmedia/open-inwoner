from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

from furl import furl

register = template.Library()


@register.inclusion_tag("components/Typography/Link.html")
def link(href, text, **kwargs):
    """
    Renders an hyperlink.

    Usage:
        {% link 'http://www.example.com' text=_('Example.com') %}
        {% link href='inbox:index' text=_('Mijn berichten') %}

    Variables:
        + href: str | where the link links to (can be url name to resolve).
        + text: str | The text that should be displayed in the link
        - active: bool | If the link is active
        - align: str | "left" or "right".
        - bold: bool | whether the link should be bold.
        - button: bool | Whether the link should appear as button.
        - data_text: str | data-text
        - data_alt_text: str | data-alt-text
        - data_icon: str | data-icon
        - data_alt_icon: str | data-alt-icon
        - download: bool | If the linked file should be downloaded.
        - extra_classes: str | Extra classes
        - hide_text: bool | whether to hide the text and use aria attribute instead.
        - icon: str | The icon that should be displayed.
        - icon_position: str | "before" or "after".
        - primary: bool | If the primary styling should be used
        - secondary: bool | If the secondary styling should be used
        - toggle: str | If set, creates a toggle for target specified in href, the value ot toggle is used as
        - toggle_exclusive: str | If set, creates a toggle group with query selector set by value.
          BEM (Block Element Modifier) modifier which is added/removed on toggle.
        - transparent: bool | Whether the button should not have a background or border.
        - social_icon: str | The icon that should be displayed from font-awesome
        - src: str | The source of the image
        - type: str | the type of button that should be used.
        - object_id: str | if href is an url name, object_id for reverse can be passed.
        - uuid: str | if href is an url name, uuid for reverse can be passed.
        - title: string | The HTML title attribute if different than the text.
        - hide_external_icon: bool | If we want to hide the extra icon for an external link
        - blank: bool | if we want the link to open in a new tab.

    Extra context:
        - base_class: string | If it is a button or a string.
        - classes: string | All additional classes that need to be added.
    """

    def get_href():
        try:
            uuid = kwargs.get("uuid")
            object_id = kwargs.get("object_id")
            reverse_kwargs = {}
            if uuid:
                reverse_kwargs.update(uuid=uuid)
            if object_id:
                reverse_kwargs.update(object_id=object_id)
            return reverse(href, kwargs=reverse_kwargs)
        except NoReverseMatch:
            pass

        return href

    def get_base_class():
        button = kwargs.get("button", False)
        return "button" if button else "link"

    def get_classes():
        base_class = get_base_class()
        classes = [base_class]

        if kwargs.get("toggle"):
            classes.append("toggle")

        for modifier_tuple in [
            ("active", False),
            ("align", ""),
            ("bold", False),
            ("icon", False),
            ("icon_position", ""),
            ("primary", False),
            ("secondary", False),
            ("transparent", False),
        ]:
            modifier, default = modifier_tuple
            modifier_class = modifier.replace("_", "-")
            value = kwargs.get(modifier, default)

            if not value:
                continue

            if type(default) is bool:
                classes.append(f"{base_class}--{modifier_class}")
                continue
            classes.append(f"{base_class}--{modifier_class}-{value}")
            classes.append(kwargs.get("extra_classes", ""))

        return " ".join(classes).strip()

    src = kwargs.get("src")
    if src and src.endswith(".svg"):
        svg_height = kwargs.pop("svg_height", None)
        if svg_height:
            kwargs["svg_height_attr"] = format_html(' height="{}"', svg_height)

    kwargs["base_class"] = get_base_class()
    kwargs["classes"] = get_classes()
    kwargs["href"] = get_href()
    kwargs["text"] = text
    return kwargs


@register.filter
def addnexturl(href, next_url):
    """
    Concatenates href & next_url.
    """
    f = furl(href)
    f.args["next"] = next_url
    return f.url
