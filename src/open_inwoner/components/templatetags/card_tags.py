from django import template

register = template.Library()


@register.inclusion_tag("components/Card/Card.html")
def card(href, title, **kwargs):
    return {**kwargs, "href": href, "title": title}


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
