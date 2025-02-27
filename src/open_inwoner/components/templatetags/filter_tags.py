from django import template

register = template.Library()


@register.inclusion_tag("components/Filter/SearchFilters.html")
def search_filters(
    search_form,
    search_filter_categories,
    search_filter_tags,
    search_filter_organizations,
    **kwargs
):
    """
    Renders the actions in a filterable table.

    Usage:
        {% search_filters search_form form_id='form_id' search_filter_categories search_filter_tags search_filter_organizations %}

    Available options:
        + search_form: BaseForm | The form that contains the fields with choices.
        + form_id: str | The id of the form.
        + search_filter_categories: bool | The config bool that defines if the categorie choices are rendered.
        + search_filter_tags: bool | The config bool that defines if the tag choices are rendered.
        + search_filter_organizations: bool | The config bool that defines if the organization choices are rendered.
    """

    open_filter_index = 0

    # Determine the initial open state based on active filters and their choices
    filters = [
        (search_filter_categories, len(search_form["categories"].field.choices), 0),
        (search_filter_tags, len(search_form["tags"].field.choices), 1),
        (
            search_filter_organizations,
            len(search_form["organizations"].field.choices),
            2,
        ),
    ]

    # Set initial_open based on which filter is active and has choices
    for filter_active, choices_len, index in filters:
        if filter_active and choices_len != 0:
            open_filter_index = index
            break  # Stop once we find the first active filter with choices

    kwargs["search_form"] = search_form
    kwargs["search_filter_categories"] = search_filter_categories
    kwargs["search_filter_tags"] = search_filter_tags
    kwargs["search_filter_organizations"] = (search_filter_organizations,)
    kwargs["open_filter_index"] = open_filter_index

    return {**kwargs}


@register.inclusion_tag("components/Filter/Filter.html")
def filter(field, **kwargs):
    """
    Renders the actions in a filterable table.

    Usage:
        {% filter field=search_form.tags form_id=form_id open_filter_index=1 index=1 %}

    Available options:
        + field: Field | The field that needs to be rendered.
        + form_id: str | The id of the form.
        + open_filter_index: int | The index of the filter that should render open.
        + index: int | The index of the current filter.
    """

    kwargs["initial_open"] = kwargs["open_filter_index"] is kwargs["index"]

    return {"field": field, **kwargs}
