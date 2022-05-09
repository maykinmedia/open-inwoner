from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("sessions/session_timeout.html", takes_context=True)
def session_timeout(context):
    session = context["request"].session
    context.update(
        {
            "expiry_age": session.get_expiry_age()
            + 1,  # Add a second to make sure the session has expired.
            "warn_time": session.get_expiry_age()
            - settings.SESSION_WARN_DELTA,
        }
    )
    return context
