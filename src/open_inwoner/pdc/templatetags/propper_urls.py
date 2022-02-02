from unicodedata import category

from django import template

register = template.Library()


@register.simple_tag()
def get_category_url(category, parent_category=None):
    if category.is_root():
        return category.get_absolute_url()

    if not parent_category:
        return category.get_absolute_url()
    return category.slug
