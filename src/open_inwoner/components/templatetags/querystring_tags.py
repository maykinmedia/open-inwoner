import logging

from django import template
from django.http import QueryDict
from django.utils.html import format_html

from furl import furl

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, *query_values, key="", value="", query=""):
    """
    Combines new items with existing querystring or overwriting an existing value.
    Useful for creating a querystring utilizing existing query parameters.

    Query parameter can be added using `key` and `value` keyword arguments or by using positional arguments alongside
    the `query` keyword argument containing a template str.

    Usage:
        {% querystring key='page' value=1 as query %}
        {% querystring user.pk 1 query='user={}&page={}' as href %}

    Variables:
        - key: str | The name of the item to add to the querystring.
        - value: str | The value of the item to add to the querystring.
        - query: str | A template string (str.format()) to apply positional arguments for.
    """

    request = context["request"]
    method = request.method
    request_dict = getattr(request, method).copy()

    # NOTE the above is risky, for example:
    # if used with assumption of GET params on a page with a Form, and it fails validation the whole POST gets dumped into the urls
    if request.method != "GET":
        # let's leave a warning for now because this tag is used elsewhere
        logger.warning(
            f"querystring-template-tag used with {request.method} and dumped all submitted form-data into urls"
        )

    if key and value:
        request_dict[key] = value

    querystring_formatted = str(query).format(*query_values)
    querydict = QueryDict(querystring_formatted)
    for query_key, query_value in querydict.items():
        request_dict[query_key] = query_value

    return format_html(request_dict.urlencode())


@register.filter
def qs_page(url, value):
    if value > 1:
        # only if not first page
        f = furl(url)
        f.args["page"] = value
        return f.url
    else:
        return str(url)
