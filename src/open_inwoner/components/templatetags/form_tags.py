from django import forms, template
from django.template.library import parse_bits
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from open_inwoner.components.utils import safe_resolve

register = template.Library()

WIDGET_TEMPLATES = {
    "CHECKBOX": "components/Form/Checkbox.html",
    "MULTIPLECHECKBOX": "components/Form/MultipleCheckbox.html",
    "DATE": "components/Form/DateField.html",
    "HIDDEN": "components/Form/Hidden.html",
    "INPUT": "components/Form/Input.html",
    "RADIO": "components/Form/MultipleRadio.html",
    "TEXTAREA": "components/Form/Textarea.html",
}


@register.tag()
def render_form(parser, token):
    """
    Rendering the form where the contents will not be the standard form elements.

    Usage:
        {% render_form form=form method="GET" %}
            <input type="text" />
        {% endrender_form %}

    Variables:
        + form: Form | This is the django form that should be rendered.
        + method: string | GET or POST, which function is needed.
        - columns: int | the number of columns that the form should have.
        - spaceless: bool | If the form element and sub elements should contain margins and paddings (not including the inputs).
        - inline: bool | If the form actions should be displayed on the same line as a field.
        - autosubmit: bool | If the form should autosubmit if the inputs are changed.
        - extra_classes: string | Extra css classes for the form.
        - form_action: string | where the form should go after submit.
        - enctype: string | set the encrypt when sending forms.
        - id: string | set an id on the form. Usefull for testing.
        - data_confirm_title: string | If a confirm dialog is shown this will be the title.
        - data_confirm_cancel: string | If a confirm dialog is shown this will be the text on the cancel button.
        - data_confirm_default: string | If a confirm dialog is shown this will be the text on the confirm button.
        - submit_text: string | The text on the submit button when the form is auto rendered.
        - secondary_href: string | The link for the secondary button when the form is auto rendered.
        - secondary_text: string | The text for the secondary button when the form is auto rendered.
        - secondary_icon: string | The icon for the secondary button when the form is auto rendered.
        - secondary_icon_position: string | The icon position for the secondary button when the form is auto rendered.

    Extra context:
        - contents: string | The html content between all the open and closing tags.
    """
    function_name = "render_form"
    nodelist = parser.parse(("endrender_form",))
    parser.delete_first_token()
    bits = token.split_contents()
    _args, kwargs = parse_bits(
        parser=parser,
        bits=bits,
        params=["context", "form", "method"],
        varargs=True,
        varkw=[],
        defaults=None,
        kwonly=[],
        kwonly_defaults=None,
        takes_context=True,
        name=function_name,
    )
    return FormNode(nodelist, **kwargs)


@register.inclusion_tag("components/Form/Form.html", takes_context=True)
def form(context, form_object, **kwargs):
    """
    Renders a form including all fields.

    Usage:
        {% form form_object=form method="GET" %}

    Variables:
        + form_object: Form | This is the django form that should be rendered.
        + method: string | GET or POST, which function is needed.
        - columns: int | the number of columns that the form should have.
        - spaceless: bool | If the form element and sub elements should contain margins and paddings (not including the inputs).
        - inline: bool | If the form actions should be displayed on the same line as a field.
        - extra_classes: string | Extra css classes for the form.
        - form_action: string | where the form should go after submit.
        - enctype: string | set the encrypt when sending forms.
        - id: string | set an id on the form. Usefull for testing.
        - data_confirm_title: string | If a confirm dialog is shown this will be the title.
        - data_confirm_cancel: string | If a confirm dialog is shown this will be the text on the cancel button.
        - data_confirm_default: string | If a confirm dialog is shown this will be the text on the confirm button.
        - submit_text: string | The text on the submit button when the form is auto rendered.
        - secondary_href: string | The link for the secondary button when the form is auto rendered.
        - secondary_text: string | The text for the secondary button when the form is auto rendered.
        - secondary_icon: string | The icon for the secondary button when the form is auto rendered.
        - secondary_icon_position: string | The icon position for the secondary button when the form is auto rendered.

    Extra context:
        - auto_render: True | Telling the template that the form should be rendered.
    """
    _context = context.flatten()
    kwargs["submit_text"] = kwargs.get("submit_text", _("Verzenden"))
    return {**_context, **kwargs, "form": form_object, "auto_render": True}


@register.simple_tag()
def autorender_field(form_object, field_name, **kwargs):
    """
    Detecting what type of field sould be rendered.
    TODO: Keep updating with new fields.

    Usage:
        {% autorender_field form field %}

    Variables:
        + form_object: Form | This is the django form that contains the field.
        + field_name: FormField | the field that needs to be rendered.
    """
    bound_field = form_object[field_name]
    field = bound_field.field

    fn = input
    tmplt = WIDGET_TEMPLATES["INPUT"]

    if type(field) == forms.fields.DateField:
        tmplt = WIDGET_TEMPLATES["DATE"]
    elif type(field) == forms.models.ModelMultipleChoiceField:
        tmplt = WIDGET_TEMPLATES["MULTIPLECHECKBOX"]
    elif type(field) == forms.fields.BooleanField:
        fn = checkbox
        tmplt = WIDGET_TEMPLATES["CHECKBOX"]
    elif type(field.widget) == forms.fields.HiddenInput:
        tmplt = WIDGET_TEMPLATES["HIDDEN"]
    elif type(field.widget) == forms.widgets.RadioSelect:
        tmplt = WIDGET_TEMPLATES["RADIO"]
    elif type(field.widget) == forms.fields.Textarea:
        tmplt = WIDGET_TEMPLATES["TEXTAREA"]

    context = fn(bound_field, **kwargs)
    return render_to_string(tmplt, context)


@register.inclusion_tag("components/Form/Error.html")
def errors(errors, **kwargs):
    """
    Displaying the form errors in a standard way.

    Usage:
        {% errors form.non_field_errors %}

    Variables:
        + errors: list | The non field errors or the field errors.
    """
    return {**kwargs, "errors": errors}


@register.inclusion_tag(WIDGET_TEMPLATES["CHECKBOX"])
def checkbox(field, **kwargs):
    """
    Displaying a checkbox.

    Usage:
        {% checkbox form.checkbox_field %}

    Variables:
        + field: Field | The field that needs to be rendered.
    """
    return {**kwargs, "field": field}


@register.inclusion_tag(WIDGET_TEMPLATES["MULTIPLECHECKBOX"])
def checkboxes(field, **kwargs):
    """
    Displaying a checkbox.

    Usage:
        {% checkbox form.checkbox_field %}

    Variables:
        + field: Field | The field that needs to be rendered.
    """
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/ChoiceCheckbox.html")
def choice_checkbox(choice, **kwargs):
    """
    Displaying a checkbox that is rendered from a multiple choice field.

    Usage:
        {% choice_checkbox form.checkbox_field %}

    Variables:
        + choice: The choice that needs to be rendered.
    """
    return {**kwargs, "choice": choice}


@register.inclusion_tag("components/Form/ChoiceRadio.html")
def choice_radio(choice, **kwargs):
    """
    Displaying a radio input that is rendered from a choice field.

    Usage:
        {% choice_radio form.radio_field %}

    Variables:
        + choice: The choice that needs to be rendered.
    """
    return {**kwargs, "choice": choice}


@register.inclusion_tag("components/Form/Input.html")
def input(field, **kwargs):
    """
    Displaying a input field. This is the fallback for every autorendered field.

    Usage:
        {% input form.field %}

    Variables:
        + field: Field | The field that needs to be rendered.
        - extra_classes: string| classes which should be added to the top-level container
    """
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/DateField.html")
def date_field(field, **kwargs):
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Search.html")
def search(field, **kwargs):
    """
    Displaying a search field.

    Usage:
        {% search form.field %}

    Variables:
        + field: Field | The field that needs to be rendered.
    """
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Textarea.html")
def textarea(field, **kwargs):
    """
    Displaying a textarea.

    Usage:
        {% textarea form.field %}

    Variables:
        + field: Field | The field that needs to be rendered.
    """
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Autocomplete.html")
def autocomplete(field, **kwargs):
    """
    Displaying an autocomplete field using @tarekraafat/autocomplete lib
    Usage:
        {% autocomplete form.field %}
    Variables:
        + field: Field | The choice field that needs to be rendered.
    """
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/Hidden.html")
def hidden(field, **kwargs):
    """
    Displaying a hidden field

    Usage:
        {% hidden form.field %}

    Variables:
        + field: Field | The choice field that needs to be rendered.
    """
    return {**kwargs, "field": field}


@register.inclusion_tag("components/Form/FormActions.html")
def form_actions(primary_text="", primary_icon=None, **kwargs):
    """
    Rendering the form actions. This may contain a primary and or secondary button.

    Usage:
        {% form_actions primary_text="Submit" %}

    Variables:
        - primary: bool | if false, hide the primary button.
        - primary_text: string | The text for the primary button.
        - primary_icon: string | The icon for the primary button.
        - single: bool | if it should be single.
        - secondary_href: string | The action when the secondary button is pressed.
        - secondary_text: string | What the text for the secondary button should be.
        - secondary_icon: string | What the icon for the secondary button should be.
        - secondary_icon_position: string | What the icon position for the secondary button should be.
        - transparent: bool | If the button should be transparent.

    Extra context:
        - primary: bool | If the primary styling should be used.
    """
    if not primary_text and primary_icon is None:
        if kwargs.get("primary", True):
            assert False, "provide primary_text or primary_icon"

    primary = kwargs.get("primary", "transparent" not in kwargs)

    return {
        **kwargs,
        "primary_text": primary_text,
        "primary_icon": primary_icon,
        "primary": primary,
    }


@register.filter(name="addclass")
def addclass(field, class_string):
    """
    Adds a class to the default field rendering of django.

    Usage:
        {{ field|addclass:"input" }}

    Varialbes:
        + field: Field | The field where the class needs to be added to.
        + class_string: string | The class that needs to be added.
    """
    return field.as_widget(attrs={"class": class_string})


class FormNode(template.Node):
    def __init__(self, nodelist, form, method, **kwargs):
        self.nodelist = nodelist
        self.form = form
        self.method = method
        self.kwargs = kwargs

    def render(self, context):
        corrected_kwargs = {
            key: safe_resolve(kwarg, context) for key, kwarg in self.kwargs.items()
        }
        output = self.nodelist.render(context)
        method = self.method.resolve(context)
        render_context = {
            "contents": output,
            "form": self.form.resolve(context),
            "request": context.get("request"),
            "method": method,
            **corrected_kwargs,
        }
        rendered = render_to_string("components/Form/Form.html", render_context)
        return rendered
