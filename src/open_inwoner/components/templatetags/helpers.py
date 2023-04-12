from django import template
from django.urls import reverse
from django.utils.html import format_html_join

register = template.Library()


@register.filter("startswith")
def startswith(text, starts):
    """
    check if a string startswith a value

    Usage:
        {{ "this is a string"|startswith:"thi" }}

    Variables:
        + text: string | the text that will be matched on.
        + value: string | what the text should start with.
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter
def is_list_instance(obj):
    """
    check if an object is a list instance

    Usage:
        {% if log_message|is_list_instance %}
            do_something
        {% endif %}

    Variables:
        + obj: object | the object we want to check if it is a list instance.
    """
    return isinstance(obj, list)


@register.simple_tag(takes_context=True)
def get_product_url(context, product):
    """
    Builds the product url build on the given product.

    Usage:
        {% get_product_url product=product as product_url %}
        {% get_product_url product=product %}

    Variables:
        + product: Product | The product we should generate the url for.
    """
    category = context.get("parent")
    if category:
        return reverse(
            "pdc:category_product_detail",
            kwargs={"category_slug": category.get_build_slug(), "slug": product.slug},
        )
    return product.get_absolute_url()


@register.simple_tag
def as_attributes(attribute_dict):
    if not attribute_dict:
        return ""
    return format_html_join(" ", '{}="{}"', attribute_dict.items())
