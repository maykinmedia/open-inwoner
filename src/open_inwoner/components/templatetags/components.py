from component_tags import template
from component_tags.template.attributes import Attribute

register = template.Library()


@register.tag
class AccessibilityHeader(template.Component):
    class Meta:
        template_name = "components/AccessibilityHeader/AccessibilityHeader.html"


@register.tag
class Header(template.Component):
    class Meta:
        template_name = "components/Header/Header.html"


@register.tag
class Logo(template.Component):
    class Meta:
        template_name = "components/Logo/Logo.html"


@register.tag
class P(template.Component):
    class Meta:
        template_name = "components/Typography/P.html"


@register.tag
class Link(template.Component):
    class IconPositionChoices(template.AttributeChoices):
        before = "before"
        after = "after"

    href = template.Attribute(required=True, as_context=True)
    extra_classes = template.Attribute(as_context=True)
    active = template.Attribute(default=False, as_context=True)
    active_class = template.Attribute(default="link--active", as_context=True)
    icon = template.Attribute(required=False, as_context=True)
    iconPosition = template.Attribute(
        choices=IconPositionChoices, default=IconPositionChoices.before, as_context=True
    )
    primary = template.Attribute(default=False, as_context=True)
    secondary = template.Attribute(default=False, as_context=True)

    class Meta:
        template_name = "components/Typography/Link.html"


@register.tag
class PrimaryNavigation(template.Component):
    class Meta:
        template_name = "components/Header/PrimaryNavigation.html"


@register.tag
class Breadcrumbs(template.Component):
    class Meta:
        template_name = "components/Header/Breadcrumbs.html"


@register.tag
class CardContainer(template.Component):
    small = template.Attribute(default=False, as_context=True)

    class Meta:
        template_name = "components/CardContainer/CardContainer.html"


@register.tag
class Card(template.Component):
    title = template.Attribute(required=True, as_context=True)
    alt = template.Attribute(as_context=True)
    src = template.Attribute(as_context=True)
    href = template.Attribute(as_context=True)

    class Meta:
        template_name = "components/Card/Card.html"
