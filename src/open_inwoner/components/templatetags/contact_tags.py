from django import template

from open_inwoner.openklant.models import OpenKlantConfig

register = template.Library()


@register.inclusion_tag("components/Contact/ContactForm.html")
def contact_form(form_object, **kwargs):
    """
    Shows a contact form

    Usage:
        {% contact_form form_object %}

    Variables:
        + form_object: Form | the form that need to be rendered.
    """
    config = OpenKlantConfig.get_solo()
    return {
        **kwargs,
        "form_object": form_object,
        "has_form_configuration": config.has_form_configuration(),
    }
