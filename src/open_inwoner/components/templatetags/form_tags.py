from django import template
from django.forms import fields
from django.template.library import parse_bits
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from open_inwoner.utils.templatetags.abstract import safe_resolve

register = template.Library()


WIDGET_TEMPLATES = {
    "INPUT": "components/Form/Input.html",
    "CHECKBOX": "components/Form/Checkbox.html",
}


@register.tag()
def render_form(parser, token):
    """
    Renders a form, allows nested content to be rendered.
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_form")
    nodelist = parser.parse(("endrender_form",))
    parser.delete_first_token()
    return FormNode(nodelist, **context_kwargs)


@register.inclusion_tag("components/Form/Form.html", takes_context=True)
def form(context, form_object, **kwargs):
    """
    Renders a form including all fields.
    """
    _context = context.flatten()
    kwargs["submit_text"] = kwargs.get("submit_text", _("Verzenden"))
    return {**_context, **kwargs, "form": form_object, "auto_render": True}


@register.simple_tag()
def autorender_field(form_object, field_name, **kwargs):
    """
    Auto renders field
    TODO: Keep updating with new fields.
    """
    bound_field = form_object[field_name]
    field = bound_field.field

    fn = input
    tmplt = WIDGET_TEMPLATES["INPUT"]

    if type(field) == fields.BooleanField:
        fn = checkbox
        tmplt = WIDGET_TEMPLATES["CHECKBOX"]

    context = fn(bound_field, **kwargs)
    return render_to_string(tmplt, context)


@register.inclusion_tag("components/Form/Error.html")
def errors(errors, **kwargs):
    return {**kwargs, "errors": errors}


@register.inclusion_tag(WIDGET_TEMPLATES["CHECKBOX"])
def checkbox(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Input.html")
def input(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Search.html")
def search(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Textarea.html")
def textarea(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/FormActions.html")
def form_actions(primary_text, primary_icon=None, **kwargs):
    return {**kwargs, "primary_text": primary_text, "primary_icon": primary_icon}


@register.filter(name="addclass")
def addclass(field, class_attr):
    return field.as_widget(attrs={"class": class_attr})


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
