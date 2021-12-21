from django import template

register = template.Library()


@register.inclusion_tag("components/Notification/Notification.html")
def notification(type, inline, title, message, action, action_text, **kwargs):
    return {
        "type": type,
        "inline": inline,
        "title": title,
        "message": message,
        "action": action,
        "action_text": action_text,
        **kwargs,
    }
