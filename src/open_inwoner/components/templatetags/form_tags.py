from django import template
from django.template.base import Node, NodeList, TemplateSyntaxError, TokenType
from django.template.library import parse_bits
from django.template.loader import render_to_string

register = template.Library()


@register.filter(name="addclass")
def addclass(field, class_attr):
    return field.as_widget(attrs={"class": class_attr})


def safe_resolve(context_item, context):
    """Resolve FilterExpressions and Variables in context if possible.  Return other items unchanged."""

    return (
        context_item.resolve(context)
        if hasattr(context_item, "resolve")
        else context_item
    )


def parse_component_with_args(parser, bits, tag_name):
    tag_args, tag_kwargs = parse_bits(
        parser=parser,
        bits=bits,
        params=["tag_name"],
        takes_context=False,
        name=tag_name,
        varargs=True,
        varkw=[],
        defaults=None,
        kwonly=[],
        kwonly_defaults=None,
    )
    return tag_kwargs


class FormNode(template.Node):
    def __init__(
        self, nodelist, form_object, method, columns=1, inline=False, **kwargs
    ):
        self.nodelist = nodelist
        self.form = form_object
        self.method = method
        self.columns = columns
        self.inline = inline
        self.kwargs = kwargs

    def render(self, context):
        corrected_kwargs = {
            key: safe_resolve(kwarg, context) for key, kwarg in self.kwargs.items()
        }
        output = self.nodelist.render(context)
        method = self.method.resolve(context).replace('"', "")
        render_context = {
            "contents": output,
            "form": self.form.resolve(context),
            "method": method,
            "columns": self.columns,
            "inline": self.inline,
            **corrected_kwargs,
        }
        rendered = render_to_string("components/Form/Form.html", render_context)
        return rendered


@register.tag()
def render_form(parser, token):
    """
    Captures contents and assigns them to variable.
    Allows capturing templatetags that don't support "as".

    Example:

        {% capture as body %}{% lorem 20 w random %}{% endcapture %}
        {% include 'components/text/text.html' with body=body only %}
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_form")
    nodelist = parser.parse(("endrender_form",))
    parser.delete_first_token()
    return FormNode(nodelist, **context_kwargs)


@register.inclusion_tag("components/Form/Error.html")
def errors(errors, **kwargs):
    return {**kwargs, "errors": errors}


@register.inclusion_tag("components/Form/Checkbox.html")
def checkbox(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Input.html")
def input(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Submit.html")
def submit(text, icon=None, **kwargs):
    return {**kwargs, "text": text, "icon": icon}
