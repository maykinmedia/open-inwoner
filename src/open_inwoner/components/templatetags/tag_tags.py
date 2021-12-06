from django import template

register = template.Library()


@register.inclusion_tag("components/Tag/Tag.html")
def tag(tags, **kwargs):
    return {**kwargs, "tags": tags}
