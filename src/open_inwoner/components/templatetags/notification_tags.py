from django import template

from open_inwoner.components.templatetags.form_tags import parse_component_with_args
from open_inwoner.utils.templatetags.abstract import ContentsNode

register = template.Library()


@register.inclusion_tag("components/Notification/Notifications.html")
def notifications(messages, **kwargs):
    """
    display multiple notifications. They will now always be positioned absolute.

    Usage:
        {% notifications messages=request.messages %}

    Variables:
        + messages: list | A list of messages that need to be displayed.
    """
    return {"messages": messages, **kwargs}


@register.inclusion_tag("components/Notification/Notification.html")
def notification(type, message, **kwargs):
    """
    Add a notification to the screen. These will be places inline.

    Usage:
        {% notification type="success" message="this is the message" closable=True %}
        {% notification type="warning" title="title" message="this is the message" action="#" action_text="Verzoek opsturen" %}

    Variables:
        + type: string | the type of notification. This will change the coloring.
        + message: string | The message for the notification.
        - title: string | The title that should be displayed.
        - action: string | The href of the button.
        - action_text: string | The text of the button.
        - closable: bool | If a close button should be shown.
    """
    return {
        "icon": kwargs.get("icon", "change_history"),
        "type": type,
        "message": message,
        **kwargs,
    }


@register.tag()
def render_notification(parser, token):
    """
    Add a notification to the screen. These will be places inline.

    Usage:
        {% render_notification type="success" %}
            this is the message
        {% endrender_notification %}

    Variables:
        + type: string | the type of notification. This will change the coloring.
        + message: string | The message for the notification.
        - title: string | The title that should be displayed.
        - action: string | The href of the button.
        - action_text: string | The text of the button.
        - closable: bool | If a close button should be shown.
    """
    bits = token.split_contents()
    context_kwargs = parse_component_with_args(parser, bits, "render_notification")
    nodelist = parser.parse(("endrender_notification",))  # End tag
    parser.delete_first_token()
    return ContentsNode(
        nodelist, "components/Notification/Notification.html", **context_kwargs
    )  # Template
