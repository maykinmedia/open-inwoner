from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("components/Action/Actions.html")
def actions(actions, request, action_form, **kwargs):
    """
    Renders the actions in a filterable table.

    Usage:
        {% actions actions=actions action_form=action_form %}

    Available options:
        + actions: Action[] | All the actions that will be shown. This should be the filtered list if filters are applied.
        + action_form: Form | The form containing the needed filters for the actions.
        - form_action: string | A url for something
        - plan: Plan | The plan that the actions belong to
    """
    kwargs.update(actions=actions, request=request, action_form=action_form)
    return kwargs


@register.simple_tag()
def get_action_edit_url(action, plan=None):
    """
    generates the correct action edit url. It can be plan action or a general action.

    Usage:
        {% get_action_edit_url action=action plan=plan %}
        {% get_action_edit_url action=action %}

    Variables:
        + action: Action | The action the url should be generated from.
        - plan: Plan | The plan the action edit url should be generated for.
    """
    if plan:
        return reverse(
            "plans:plan_action_edit",
            kwargs={"plan_uuid": plan.uuid, "uuid": action.uuid},
        )
    return reverse("accounts:action_edit", kwargs={"uuid": action.uuid})


@register.filter()
def is_connected(action, user):
    return action.is_connected(user)
