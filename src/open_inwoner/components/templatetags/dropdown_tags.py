from django import template

register = template.Library()


@register.inclusion_tag("components/Dropdown/Dropdown.html")
def dropdown(text, items, **kwargs):
    kwargs["text"] = text
    kwargs["items"] = items

    return {
        **kwargs,
    }
