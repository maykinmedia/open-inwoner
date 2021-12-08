from django import template
from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.inclusion_tag("components/Card/Card.html")
def card(href, title, **kwargs):
    return {**kwargs, "href": href, "title": title}


@register.tag
def render_card(parser, token):
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_card")
    nodelist = parser.parse(("endrender_card",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Card/Card.html", **context_kwargs)


@register.inclusion_tag("components/Card/CategoryCard.html")
def category_card(title, products, **kwargs):
    return {**kwargs, "products": products, "title": title}


@register.inclusion_tag("components/Card/ProductCard.html")
def product_card(title, description, href, **kwargs):
    return {**kwargs, "description": description, "title": title, "href": href}


@register.inclusion_tag("components/Card/CardContainer.html")
def card_container(categories=[], subcategories=[], products=[], **kwargs):
    if categories is None and subcategories is None and products is None:
        assert False, "provide categories, subcategories or products"
    return {
        **kwargs,
        "categories": categories,
        "subcategories": subcategories,
        "products": products,
    }
