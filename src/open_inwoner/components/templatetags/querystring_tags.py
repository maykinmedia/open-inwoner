from django import template
from django.http import QueryDict
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, *query_values, key="", value="", query=""):
    """
    Combines new items with existing querystring.
    Useful for creating a querystring utilizing existing query parameters.

    Query parameter can be added using `key` and `value` keyword arguments or by using positional arguments alongside
    the `query` keyword argument containing a template str.

    Example:
        {% querystring key='page' value=1 as query %}
        {% querystring user.pk 1 query='user={}&page={}' as href %}
    Available options:
        - key, optional str: The name of the item to add to the querystring.
        - value, optional str: The value of the item to add to the querystring.
        - query, optional str: A template string (str.format()) to to apply positional arguments for.
    """
    request = context["request"]
    method = request.method
    request_dict = getattr(request, method).copy()

    if key and value:
        request_dict[key] = value

    querystring_formatted = str(query).format(*query_values)
    querydict = QueryDict(querystring_formatted)
    for query_key, query_value in querydict.items():
        request_dict[query_key] = query_value

    return format_html(request_dict.urlencode())
