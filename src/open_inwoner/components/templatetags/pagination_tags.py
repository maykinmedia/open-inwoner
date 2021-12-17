from django import template

register = template.Library()


@register.inclusion_tag("components/Pagination/Pagination.html")
def pagination(page_obj, paginator, request, **kwargs):
    """
    page_obj: Default django page object
    get_paginator_dict: Default django get_paginator_dict
    request: The django request (this will be for the querystring tag. So it is not used yet)

    {% pagination page_obj=page_obj get_paginator_dict=get_paginator_dict request=request %}
    """
    return {"page_obj": page_obj, "get_paginator_dict": paginator, "request": request, **kwargs}
