import celery

from open_inwoner.celery import app

from .notifications import collect_notifications, process_notifications


@app.task
def schedule_user_notifications(notify_about: str, channel: str):
    """
    Args:
        notify_about: the topic of the notifications (e.g. "plans", "actions")
        channel: the communication channel (e.g. "email")
    """
    # Note: the return value of `collect_notifications` is passed as the first
    # (positional) argument to `process_notifications` in `celery.chain()`
    result = celery.chain(
        collect_notifications.s(notify_about=notify_about),
        process_notifications.s(notify_about=notify_about, channel=channel),
    ).apply_async()

    return result.get()
