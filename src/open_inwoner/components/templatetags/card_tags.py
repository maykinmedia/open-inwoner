from django import template

from ...pdc.models import Category, Product
from ...utils.templatetags.abstract import ContentsNode
from .form_tags import parse_component_with_args

register = template.Library()


@register.inclusion_tag("components/Card/Card.html")
def card(href, title, **kwargs):
    """
    Render in a card. Only using variables.

    Usage:
        {% card href="https://maykinmedia.nl" %}

    Variables:
        - href: url | where the card links to.
        - title: string | this will be the card title.
        - alt: string | the alt of the header image.
        - direction: string | can be set to "horizontal" to show contents horizontally.
        - src: string | the src of the header image.
        - tinted: bool | whether to use gray as background color.
    """
    return {**kwargs, "href": href, "title": title}


@register.tag
def render_card(parser, token):
    """
    Render in a card. Using nested elements.

    Usage:
        {% render_card %}
            <h1 class="h1">{% trans 'Welkom' %}</h1>
        {% endrender_card %}

    Extra context:
        - contents: string (HTML) | this is the context between the render_card and endrender_card tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_card")
    nodelist = parser.parse(("endrender_card",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Card/RenderCard.html", **context_kwargs)


@register.inclusion_tag("components/Card/CategoryCard.html")
def category_card(category: Category, **kwargs):
    """
    Cards that are tailored for displaying the category with all the products listed inside.

    Usage:
        {% category_card title=category.title products=category.products.all %}

    Variables:
        + title: string | this will be the card title.
        + products: Product[] | products to render.
        - href: url | where the card links to.
    """
    return {**kwargs, "category": category}


@register.inclusion_tag("components/Card/ProductCard.html")
def product_card(product: Product, **kwargs):
    """
    A card for rendering a product card.

    Usage:
        {% product_card title=product.title description=product.description href=product.get_absolute_url %}

    Variables:
        + title: string | this will be the card title.
        + description: string | this will be the card description.
        + href: url | where the card links to.
    """
    return {**kwargs, "product": product}


@register.inclusion_tag("components/Card/CardContainer.html")
def card_container(categories=[], subcategories=[], products=[], **kwargs):
    """
    A card container where the category card or product card will be rendered in.

    Usage:
    {% card_container categories=categories %}

    Variables:
    - categories: Category[] | categories to render. (Optional)
    - subcategories: Category[] | subcategories to render. (Optional)
    - products: Product[] | products to render. (Optional)
    """
    if categories is None and subcategories is None and products is None:
        assert False, "provide categories, subcategories or products"

    return {
        **kwargs,
        "categories": categories,
        "subcategories": subcategories,
        "products": products,
    }


@register.tag()
def render_card_container(parser, token):
    """
    Nested content supported.

    Usage:
        {% render_card_container %}
            {% card href='https://www.example.com' title='example.com' %}
        {% endrender_card_container %}

    Variables:
        Supports all options from card, but optional.

     Extra context:
         - contents: string (HTML) | this is the context between the render_card and endrender_card tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_list")
    nodelist = parser.parse(("endrender_card_container",))  # End tag
    parser.delete_first_token()
    return ContentsNode(
        nodelist, "components/Card/CardContainer.html", **context_kwargs
    )  # Template
