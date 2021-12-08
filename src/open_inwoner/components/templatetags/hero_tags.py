from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.inclusion_tag("components/Hero/Hero.html")
def hero(image_src, image_alt=_('Decorative image'), **kwargs):
    return {
        **kwargs,
        "image_alt": image_alt,
        "image_src": image_src,
    }
