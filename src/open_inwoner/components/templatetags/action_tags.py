from django import template

register = template.Library()


@register.inclusion_tag("components/Action/Actions.html")
def actions(actions, **kwargs):
    """
    Renders the actions in a filterable table.

    Usage:
        {% actions actions=actions action_form=action_form %}

    Available options:
        + actions: Action[] | All the actions that will be shown. This should be the filtered list if filters are applied.
        + action_form: Form | The form containing the needed filters for the actions.
    """
    kwargs.update(actions=actions)
    return kwargs
