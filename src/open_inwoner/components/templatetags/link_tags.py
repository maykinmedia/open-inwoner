from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.inclusion_tag("components/Typography/Link.html")
def link(href, **kwargs):
    """
    href: url | where the link links to (can be url name).
    bold: bool | whether the link should be bold. (Optional)
    uuid: str | if href is an url name, kwargs for reverse can be passed (Optional).
    reverse_kwargs: dict | if href is an url name, kwargs for reverse can be passed (Optional).
    download: bool | If the linked file should be downoaded. (Optional)
    extra_classes: string | Extra classes (Optional)
    active: bool | If the link is active (Optional)
    align: "left" or "right" | What the text align should be (Optional)
    icon_position: "before" or "after" | If the icon is before or after the text (Optional)
    primary: bool | If the primary styling should be used (Optional)
    secondary: bool | If the secondary styling should be used (Optional)
    src: string | The source of the image (Optional)
    social_icon: string | The icon that should be displayed from font-awesome (Optional)
    icon: string | The icon that should be displayed (Optional)
    text: string | The text that should be displayed in the link (Optional)
    hide_text: bool | whether to hide the text and use aria attribute instead. (Optional).
    type: string | the type of button that should be used. (Optional)
    data_text: string | data-text (Optional)
    data_alt_text: string | data-alt-text (Optional)
    data_icon: string | data-icon (Optional)
    data_alt_icon: string | data-alt-icon (Optional)
    """
    try:
        uuid = kwargs.get("uuid")
        reverse_kwargs = {}
        if uuid:
            reverse_kwargs.update(uuid=uuid)
        href = reverse(href, kwargs=reverse_kwargs)
    except NoReverseMatch:
        pass

    kwargs["icon_position"] = kwargs.get("icon_position", kwargs.get("iconPosition"))
    kwargs["href"] = href

    return kwargs
