from django import template

register = template.Library()


@register.simple_tag
def querystring(request, key, value):
    request_dict = request.GET.copy()
    request_dict[key] = value
    return request_dict.urlencode()
