from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.inclusion_tag("components/Typography/Link.html")
def link(href, **kwargs):
    """
    href: url | where the link links to (can be url name).

    bold: bool | whether the link should be bold.
    download: bool | whether the link should be downloaded instead of linked to. (Optional)
    extra_classes: string | additional CSS classes.
    hide_text: bool | whether to hide the text and use aria attribute instead. (Optional).
    icon: string | the icon that you want to display. (Optional)
    icon_position: "before" or "after" | where the icon should be positioned to the text. (Optional)
    primary: bool | if the primary colors should be used. (Optional)
    reverse_kwargs: dict | if href is an url name, kwargs for reverse can be passed (Optional).
    secondary: bool | if the secondary colors should be used. (Optional)
    social_icon: string | the social icon that you want to display. (Optional)
    text: string | this will be the link text. (Optional)
    type: string | the type of button that should be used. (Optional)
    """
    try:
        reverse_kwargs = kwargs.get("reverse_kwargs")
        href = reverse(href, kwargs=reverse_kwargs)
    except NoReverseMatch:
        pass

    kwargs["icon_position"] = kwargs.get("icon_position", kwargs.get("iconPosition"))
    kwargs["href"] = href

    return kwargs
