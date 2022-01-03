from django import template

from ...pdc.models import Category, Product
from ...utils.templatetags.abstract import ContentsNode
from .form_tags import parse_component_with_args

register = template.Library()


@register.inclusion_tag("components/Card/Card.html")
def card(href, title, **kwargs):
    """
    href: url | where the card links to. (Optional)
    title: string | this will be the card title. (Optional)

    alt: string | the alt of the header image. (optional)
    direction: string | can be set to "horizontal" to show contents horizontally (Optional).
    src: string | the src of the header image. (optional)
    tinted: bool | whether to use gray as background color. (Optional)
    """
    return {**kwargs, "href": href, "title": title}


@register.tag
def render_card(parser, token):
    """
    Supports all options from card.
    Nested content supported.
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_card")
    nodelist = parser.parse(("endrender_card",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Card/RenderCard.html", **context_kwargs)


@register.inclusion_tag("components/Card/CategoryCard.html")
def category_card(category: Category, **kwargs):
    """
    Renders a card prepopulated based on `category`.

    Example:
        {% category_card category %}

    Available options:

        - category, Category: the category to render card for.
    """
    return {**kwargs, "category": category}


@register.inclusion_tag("components/Card/ProductCard.html")
def product_card(product: Product, **kwargs):
    """
    Renders a card prepopulated based on `product`.

    Example:
        {% product_card product %}

    Available options:

        - product, Product: the product to render card for.
    """
    return {**kwargs, "product": product}


@register.inclusion_tag("components/Card/CardContainer.html")
def card_container(categories=[], subcategories=[], products=[], **kwargs):
    """
    categories: Category[] | categories to render.
    subcategories: Category[] | subcategories to render.
    products: Product[] | products to render.
    """
    if categories is None and subcategories is None and products is None:
        assert False, "provide categories, subcategories or products"
    return {
        **kwargs,
        "categories": categories,
        "subcategories": subcategories,
        "products": products,
    }
