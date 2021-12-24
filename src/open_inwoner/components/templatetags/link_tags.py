from django import template
from django.http import QueryDict
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def get_query_string(context, query, *values):
    """
    Combines query with existing querystring.
    Usefull for creating querystrings utizling exist query parameters.

    query: str | The querystring to add (without "?).
    """
    request = context["request"]
    method = request.method

    rquerydict = getattr(request, method).copy()
    rquerydict._mutable = True

    query_string = str(query).format(*values)
    qquerydict = QueryDict(query_string)
    for key, value in qquerydict.items():
        rquerydict[key] = value

    rquerydict._mutable = False
    return f"?{rquerydict.urlencode()}"


@register.inclusion_tag("components/Typography/Link.html")
def link(href, **kwargs):
    """
    Renders an hyperlink.

    Example:
        {% link 'http://www.example.com' %}
        {% link 'http://www.example.com' text=_('Example.com') %}
        {% link href='accounts:inbox' text=_('Mijn berichten') %}

    Available options:

        - href, str: where the link links to (can be url name to resolve).

        - active, optional bool: If the link is active
        - align, optional str: "left" or "right".
        - bold, optional bool: whether the link should be bold.
        - button, optional bool: Whether the link should appear as button.
        - data_text, optional str: data-text
        - data_alt_text, optional str: data-alt-text
        - data_icon, optional str: data-icon
        - data_alt_icon, optional str: data-alt-icon
        - download, optional bool: If the linked file should be downoaded.
        - extra_classes, optional str: Extra classes
        - hide_text, optional bool: whether to hide the text and use aria attribute instead.
        - icon, optional str: The icon that should be displayed.
        - icon_position, optional str: "before" or "after".
        - primary, optional bool: If the primary styling should be used
        - secondary, optional bool: If the secondary styling should be used
        - social_icon, optional str: The icon that should be displayed from font-awesome
        - src, optional str: The source of the image
        - text, optional str: The text that should be displayed in the link
        - type, optional str: the type of button that should be used.
        - uuid, optional str: if href is an url name, kwargs for reverse can be passed.
    """

    def get_href():
        try:
            uuid = kwargs.get("uuid")
            reverse_kwargs = {}
            if uuid:
                reverse_kwargs.update(uuid=uuid)
            return reverse(href, kwargs=reverse_kwargs)
        except NoReverseMatch:
            pass

        return href

    def get_base_class():
        button = kwargs.get("button", False)
        return "button" if button else "link"

    def get_classes():
        base_class = get_base_class()
        classes = [base_class]

        for modifier_tuple in [
            ('active', False),
            ('align', ''),
            ('bold', False),
            ('icon_position', ''),
            ('primary', False),
            ('secondary', False)
        ]:
            modifier, default = modifier_tuple
            modifier_class = modifier.replace('_', '-')
            value = kwargs.get(modifier, default)

            if not value:
                continue

            if type(default) is bool:
                classes.append(f"{base_class}--{modifier_class}")
            classes.append(f"{base_class}--{modifier_class}-{value}")
            classes.append(kwargs.get('extra_classes', ''))

        return " ".join(classes).strip()

    kwargs["base_class"] = get_base_class()
    kwargs["classes"] = get_classes()
    kwargs["href"] = get_href()
    return kwargs
