from django import template
from django.urls import reverse

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
            kwargs={"theme_slug": category.get_build_slug(), "slug": product.slug},
        )
    return product.get_absolute_url()
