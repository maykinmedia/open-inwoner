from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.inclusion_tag("components/Typography/Link.html")
def link(href, **kwargs):
    """
    href: url | where the link links to.

    text: string | this will be the link text. (Optional)
    download: bool | whether the link should be downloaded instead of linked to. (Optional)
    extra_classes: string | additional CSS classes.
    icon_position: "before" or "after" | where the icon should be positioned to the text. (Optional)
    primary: bool | if the primary colors should be used. (Optional)
    secondary: bool | if the secondary colors should be used. (Optional)
    icon: string | the icon that you want to display. (Optional)
    social_icon: string | the social icon that you want to display. (Optional)
    type: string | the type of button that should be used. (Optional)
    """
    try:
        href = reverse(href)
    except NoReverseMatch:
        pass

    kwargs["href"] = href

    return kwargs
