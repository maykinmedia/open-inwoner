from django import template

register = template.Library()


@register.inclusion_tag("components/Button/Button.html")
def button(text, **kwargs):
    """
    text: this will be the button text
    hide_text: bool | whether to hide the text and use aria attribute instead. (Optional).
    href: where the button links to (Optional)
    icon: the icon that you want to display (Optional)
    """
    return {**kwargs, "text": text}
