import json

from django import template
from django.urls import reverse
from django.utils.html import escape

from open_inwoner.accounts.choices import StatusChoices

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
        - plan: Plan | The plan that the actions belong to.
        - show_plans: bool | If plan functionality is enabled
    """
    kwargs.update(
        actions=actions,
        request=request,
        action_form=action_form,
        show_plans=kwargs.get("show_plans", True),
    )
    return kwargs


@register.inclusion_tag("components/Action/ActionStatusButton.html")
def action_status_button(action, request, plan=None, **kwargs):
    """
    Renders the action status as a htmx-enabled button and dropdown.

    Usage:
        {% action_status_button action=action plan=plan request=request %}

    Available options:
        + action: Action | The actions that will be shown.
        + request: Request | The django request object.
        - plan: Plan | The plan that the actions belong to.

    Extra context:
        - swap_target_id: string | ID of the swappable element
        - text: string | The label for the button.
        - icon: string | The icon for the button.
        - class: str | Additional classes.
        - choices: List[dict] | Choices with context for the buttons in the status dropdown.
    """
    if plan:
        action_url = reverse(
            "plans:plan_action_edit_status",
            kwargs={"plan_uuid": plan.uuid, "uuid": action.uuid},
        )
    else:
        action_url = reverse(
            "accounts:action_edit_status", kwargs={"uuid": action.uuid}
        )

    swap_target_id = f"actions_{action.pk}__status"
    choices = [
        {
            "text": label,
            "icon": icon,
            "class": f"actions__status-button actions__status-{value}",
            "selected": (value == action.status),
            # TODO enable this disabled disabled option after fixing the style issue
            # "disabled": (value == action.status),
            "extra_attributes": {
                "hx-post": action_url,
                "hx-swap": "outerHTML",
                "hx-vals": escape(json.dumps({"status": value})),
                "hx-target": f"#{swap_target_id}",
            },
        }
        for value, label, icon in StatusChoices.choices_with_icons()
    ]

    kwargs[
        "class"
    ] = f"actions__status-selector actions__status-selector--{action.status}"
    kwargs.update(
        action=action,
        request=request,
        swap_target_id=swap_target_id,
        icon=action.get_status_icon(),
        text=action.get_status_display(),
        choices=choices,
    )
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


@register.simple_tag()
def get_action_delete_url(action, plan=None):
    """
    generates the correct action delete url. It can be plan action or a general action.

    Usage:
        {% get_action_delete_url action=action plan=plan %}
        {% get_action_delete_url action=action %}

    Variables:
        + action: Action | The action the url should be generated from.
        - plan: Plan | The plan the action edit url should be generated for.
    """
    if plan:
        return reverse(
            "plans:plan_action_delete",
            kwargs={"plan_uuid": plan.uuid, "uuid": action.uuid},
        )
    return reverse("accounts:action_delete", kwargs={"uuid": action.uuid})


@register.simple_tag()
def get_action_history_url(action, plan):
    """
    Generates the correct action history url for plans.

    Usage:
        {% get_action_history_url action=action plan=plan %}

    Variables:
        + action: Action | The action the url should be generated from.
        + plan: Plan | The plan the action history url should be generated for.
    """
    return reverse(
        "plans:plan_action_history",
        kwargs={"plan_uuid": plan.uuid, "uuid": action.uuid},
    )


@register.filter()
def is_connected(action, user):
    """
    see if the given user is connected to the action.

    Usage:
        {% if action|is_connected:request.user %}
        {{ action|is_connected:request.user }}

    Variables:
        + action: Action | The action we check if the user has access.
        + user: User | The user we check if has access to the action.
    """
    return action.is_connected(user)
