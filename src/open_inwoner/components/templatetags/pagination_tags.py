from django import template

register = template.Library()


@register.inclusion_tag("components/Pagination/Pagination.html")
def pagination(page_obj, paginator, request, lookaround=3, **kwargs):
    """
    page_obj: Default django page object
    paginator: Default django paginator
    request: The django request (this will be for the querystring tag. So it is not used yet)
    lookaround: int | The amount of pages to render around the active page number (default=3)

    {% pagination page_obj=page_obj paginator=paginator request=request %}
    """
    page_numbers = [
        page_obj.number - lookaround + i
        for i in range(lookaround * 2 + 1)
        if (1 <= page_obj.number - lookaround + i <= paginator.num_pages)
    ]

    return {
        "page_obj": page_obj,
        "paginator": paginator,
        "request": request,
        "page_numbers": page_numbers,
        **kwargs,
    }
