from django import template

"""
Tags for testing template-tag related functionality
"""

register = template.Library()


@register.simple_tag
def simple_test_tag(*args, **kwargs):
    return "I'm a simple tag!"


@register.inclusion_tag("components/Testing/InclusionTag.html")
def inclusion_test_tag(content):
    return {
        "content": content,
    }


@register.inclusion_tag("components/Testing/NestedTag.html")
def nested_test_tag(title, content="default", **kwargs):
    return {
        "title": title,
        "content": content,
    }
