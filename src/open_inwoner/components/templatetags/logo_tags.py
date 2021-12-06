from django import template

register = template.Library()


@register.inclusion_tag("components/Logo/Logo.html")
def logo(src, alt, **kwargs):
    return {**kwargs, "src": src, "alt": alt}
