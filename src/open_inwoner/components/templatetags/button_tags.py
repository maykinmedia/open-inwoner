from django import template

register = template.Library()


@register.inclusion_tag("components/Button/Button.html")
def button(text, **kwargs):
    """
    text: this will be the button text
    href: where the button links to (Optional)
    icon: the icon that you want to display (Optional)
    """
    return {**kwargs, "text": text}
