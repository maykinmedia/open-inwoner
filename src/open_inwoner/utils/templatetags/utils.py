from django import template
from django.conf import settings
from django.utils.html import format_html

from humanfriendly import format_size

register = template.Library()


class CaptureNode(template.Node):
    def __init__(self, nodelist, var_name):
        self.nodelist = nodelist
        self.var_name = var_name

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.var_name] = output
        return ""


@register.tag
def capture(parser, token):
    """
    Captures contents and assigns them to variable.
    Allows capturing templatetags that don't support "as".

    Usage:
        {% capture as body %}{% lorem 20 w random %}{% endcapture %}
        {% include 'components/text/text.html' with body=body only %}
    """
    args = token.split_contents()
    if len(args) < 3 or args[-2] != "as":
        raise template.TemplateSyntaxError(
            "'capture' tag requires a variable name after keyword 'as'."
        )
    var_name = args[-1]
    nodelist = parser.parse(("endcapture",))
    parser.delete_first_token()
    return CaptureNode(nodelist, var_name)


@register.filter()
def multiply(value, times):
    """
    Multiplies value by times.
    """
    return value*times

@register.simple_tag
def placekitten(width=800, height=600):
    """
    Renders a "placekitten" placeholder image.

    Usage:
        {%placekitten %}
        {%placekitten 200 200 %}
    """
    return format_html('<img src="{}" />'.format(placekitten_src(width, height)))


@register.simple_tag
def placekitten_src(width=800, height=600):
    """
    Return a "placekitten" placeholder image url.

    Usage:
        {% placekitten_src as src %}
        {% placekitten_src 200 200 as mobile_src %}
        {% include 'components/image/image.html' with mobile_src=mobile_src src=src alt='placekitten' only %}
    """
    return "//placekitten.com/{}/{}".format(width, height)


@register.simple_tag
def version():
    return settings.RELEASE


@register.simple_tag(name="dir")
def template_dir(value):
    """
    Lists all the available variables and methods for the given value

    Usage:
        {% dir request %}
        {% dir "string" %}
    """
    return dir(value)


@register.filter
def readable_size(value):
    return format_size(value)
