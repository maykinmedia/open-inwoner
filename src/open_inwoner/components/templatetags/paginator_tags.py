from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.inclusion_tag('components/Paginator/Paginator.html')
def paginator(paginator_context):
    """
    paginator_context: dict | Return value from get_paginator_dict.
    """
    return paginator_context


def get_paginator_dict(request, object_list, per_page, current_page=None, lookaround=1):
    """
    object_list: list | The items to paginate.
    per_page: int | Items per page.
    current_page: int | The current page (Optional, defaults to request.GET[page]).
    lookaround: int | The amount of pages to render around the active page number.
    """

    #
    # Create paginator.
    #

    p = Paginator(object_list, per_page)

    #
    # Get current page.
    #

    # Default.
    if current_page == None:
        try:
            current_page = int(request.GET.get('page', '1'))
        except AttributeError:
            pass

    # Support first last.
    if current_page == 'first':
        current_page = 1
    elif current_page == 'last':
        current_page = p.num_pages
    elif current_page > p.num_pages:
        current_page = p.num_pages
    elif current_page < 1:
        current_page = 1

    print(2, current_page)

    #
    # Page numbers.
    #

    # Page numbers to render based on lookaround.
    page = p.get_page(current_page)
    page_numbers = [
        current_page - lookaround + i
        for i in range(lookaround * 2 + 1)
        if (1 < current_page - lookaround + i < p.num_pages)
    ]

    return {
        'is_paginated': len(object_list) <= per_page,
        'object_list': object_list,
        'page_numbers': page_numbers,
        'page_obj': page,
        'paginator': p,
        'request': request,
    }
