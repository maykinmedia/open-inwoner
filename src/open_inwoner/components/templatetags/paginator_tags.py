from django import template
from django.core.paginator import Paginator

register = template.Library()


@register.inclusion_tag('components/Paginator/Paginator.html', takes_context=True)
def paginator(context, object_list, per_page, current_page=None, lookaround=1):
    """
    object_list: list | The items to paginate.
    per_page: int | Items per page.
    current_page: int | The current page (Optional, defaults to request.GET[page]).
    lookaround: int | The amount of pages to render around the active page number.
    """

    # The current page (Optional, defaults to request.GET[page]).
    if not current_page:
        try:
            request = context['request']
            current_page = int(request.GET.get('page', 1))
        except AttributeError:
            pass

    p = Paginator(object_list, per_page)

    if current_page == 'first':
        current_page = 1
    elif current_page == 'last':
        current_page = p.num_pages
    elif current_page > p.num_pages:
        current_page = p.num_pages
    elif current_page < 1:
        current_page = 1

    page = p.get_page(current_page)
    page_numbers = [
        current_page - lookaround + i
        for i in range(lookaround * 2 + 1)
        if (1 < current_page - lookaround + i < p.num_pages)
    ]


    return {
        'page_numbers': page_numbers,
        'is_paginated': True,
        'object_list': len(object_list) <= per_page,
        'paginator': p,
        'page_obj': page,
    }
