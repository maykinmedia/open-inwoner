from django import template
from django.urls import NoReverseMatch, reverse

from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.tag
def dropdown(parser, token):
    """
    Creating a dropdown. This is for hidden menus.
    Usage:
        {% dropdown %}
            <div class="dropdown__item">
                {% button text="button 1" %}
            </div>
            <div class="dropdown__item">
                {% button text="button 2" %}
            </div>
        {% enddropdown %}

    Variables:
        - icon: string | The icon that should be shown in the dropdown button.
        - text: string | The text that should be shown in the dropdown button.

    Extra context:
        - contents: string (HTML) | this is the context between the dropdown and enddropdown tags
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "dropdown")
    nodelist = parser.parse(("enddropdown",))
    parser.delete_first_token()
    return ContentsNode(nodelist, "components/Dropdown/Dropdown.html", **context_kwargs)
