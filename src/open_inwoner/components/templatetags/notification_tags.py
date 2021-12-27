from django import template

register = template.Library()


@register.inclusion_tag("components/Notification/Notifications.html")
def notifications(messages, **kwargs):
    return {"messages": messages, **kwargs}


@register.inclusion_tag("components/Notification/Notification.html")
def notification(type, title, message, **kwargs):
    return {
        "type": type,
        "title": title,
        "message": message,
        **kwargs,
    }
