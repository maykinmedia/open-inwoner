from django import template

register = template.Library()


@register.inclusion_tag("components/Button/Button.html")
def button(text, **kwargs):
    return {**kwargs, "text": text}
