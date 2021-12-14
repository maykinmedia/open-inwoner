from django import template

register = template.Library()


@register.inclusion_tag("components/Pagination/Pagination.html")
def pagination(page_obj, paginator, request, **kwargs):
    """
    page_obj: Default django page object
    paginator: Default django paginator
    request: The django request (this will be for the querystring tag. So it is not used yet)

    {% pagination page_obj=page_obj paginator=paginator request=request %}
    """
    return {"page_obj": page_obj, "paginator": paginator, "request": request, **kwargs}
