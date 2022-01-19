from django import template

register = template.Library()


@register.inclusion_tag("components/Tag/Tag.html")
def tag(tags, **kwargs):
    """
    Displaying a Tag

    Usage:
        {% tag tags=Tag.objects.all %}

    Variables:
        + tags: Tag | a tag.
    """
    return {**kwargs, "tags": tags}
