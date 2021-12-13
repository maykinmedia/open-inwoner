from django import template
from django.template.loader import render_to_string


class ContentsNode(template.Node):
    def __init__(self, nodelist, template_name, **kwargs):
        self.kwargs = kwargs
        self.nodelist = nodelist
        self.template_name = template_name

    def render(self, context):
        corrected_kwargs = {
            key: safe_resolve(kwarg, context) for key, kwarg in self.kwargs.items()
        }
        output = self.nodelist.render(context)
        render_context = {
            "contents": output,
            **corrected_kwargs,
        }
        rendered = render_to_string(self.template_name, render_context)
        return rendered


def safe_resolve(context_item, context):
    """Resolve FilterExpressions and Variables in context if possible.  Return other items unchanged."""

    return (
        context_item.resolve(context)
        if hasattr(context_item, "resolve")
        else context_item
    )
