from django import template

from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

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
    return ContentsNode(nodelist, "components/Card/Card.html", **context_kwargs)


@register.inclusion_tag("components/Card/CategoryCard.html")
def category_card(title, products, **kwargs):
    """
    title: string | this will be the card title. (Optional)
    products: Product[] | products to render.
    href: url | where the card links to. (Optional)
    """
    return {**kwargs, "products": products, "title": title}


@register.inclusion_tag("components/Card/ProductCard.html")
def product_card(title, description, href, **kwargs):
    """
    title: string | this will be the card title. (Optional)
    description: string | this will be the card description. (Optional)
    """
    return {**kwargs, "description": description, "title": title, "href": href}


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
