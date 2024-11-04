import celery

from open_inwoner.celery import app
from open_inwoner.configurations.models import SiteConfiguration

from .notifications import collect_notifications, process_notifications


def _notifications_enabled(notification_type: str) -> bool:
    """
    Check if notifications of a certain type are globally enabled by staff users
    """
    config = SiteConfiguration.get_solo()
    notification_enable_setting = f"notifications_{notification_type}_enabled"
    return getattr(config, notification_enable_setting)


@app.task
def schedule_user_notifications(notify_about: str, channel: str):
    """
    Args:
        notify_about: the topic of the notifications (e.g. "plans", "actions")
        channel: the communication channel (e.g. "email")
    """
    if not _notifications_enabled(notify_about):
        return

    # Note: the return value of `collect_notifications` is passed as the first
    # (positional) argument to `process_notifications` in `celery.chain()`
    celery.chain(
        collect_notifications.s(notify_about=notify_about),
        process_notifications.s(notify_about=notify_about, channel=channel),
    ).apply_async()
