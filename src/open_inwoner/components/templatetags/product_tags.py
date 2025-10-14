from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _

from open_inwoner.utils.html import get_product_rendered_content

register = template.Library()


@register.inclusion_tag("components/Product/finder.html", takes_context=True)
def product_finder(
    context, condition, form, form_action=None, primary_text=None, **kwargs
):
    """
    Renders the actions in a filterable table.

    Usage:
        {% product_finder condition=condition form=form %}
        {% product_finder condition=condition form=form form_action="/finder/" %}

    Available options:
        + condition: ProductCondition | The product condition that should be answered
        + form: Form | The form for the questions.
        - form_action: string | A url for something
    """
    if not primary_text:
        primary_text = _("Volgende")
    try:
        form_action = reverse(form_action)
    except NoReverseMatch:
        form_action = "."

    kwargs.update(
        condition=condition,
        form=form,
        form_action=form_action,
        primary_text=primary_text,
        configurable_text=context["configurable_text"],
    )
    return kwargs


@register.filter("product_rendered_content")
def product_rendered_content(product):
    """
    Returns rendered content for a product.

    Usage:
        {{ object|product_rendered_content }}

    Variables:
        + product: Product | The product object
    """
    rendered_content = get_product_rendered_content(product)

    return rendered_content
