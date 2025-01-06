from typing import Any, Callable

import celery

from open_inwoner.celery import app

from .actions import (
    collect_notifications_about_expiring_actions,
    notify_user_about_expiring_actions,
)
from .messages import collect_notifications_about_messages, notify_user_about_messages
from .plans import (
    collect_notifications_about_expiring_plans,
    notify_user_about_expiring_plans,
)
from .typing import Notifier


@app.task
def collect_notifications(notify_about: str) -> list[dict]:
    """
    Dispatch to collect and return data for notifications

    Args:
        notify_about: the topic of the notifications (messages, expiring plans etc.)
    """
    collect_notifications_data: Callable = _collectors[notify_about]

    notifications = collect_notifications_data()

    return notifications


@app.task
def process_notifications(notifications: list[dict], notify_about: str, channel: str):
    """
    Create a group of tasks to notify each user of specific objects

    Args:
        notifications: list with dataclass objects about notifications
        notify_about: the topic of the notifications (messages, expiring plans etc.)
        channel: the communication channel (email, sms etc.)
    """
    task = _tasks[channel]

    task_group = celery.group(
        task.s(
            receiver_id=notification["receiver_id"],
            object_ids=notification["object_ids"],
            notify_about=notify_about,
        )
        for notification in notifications
    )

    task_group.apply_async()


@app.task
def send_email(
    receiver_id: int,
    object_ids: list[int],
    notify_about: str,
):
    """
    Dispatch to notify user with email about specific objects

    Args:
        receiver_id: the id of the email's recipient
        object_ids: the topic of the email (messages, expiring plans, etc.) in
            the form of a list of id's for later reconstruction of QuerySet
        notify: the specific function used to notify the user, depending
            on which objects we notify about
    """
    notify: Notifier = _notifiers[notify_about]

    notify(
        receiver_id=receiver_id,
        object_ids=object_ids,
        channel="email",
    )


_collectors: dict[str, Callable[..., list[dict]]] = {
    "actions": collect_notifications_about_expiring_actions,
    "messages": collect_notifications_about_messages,
    "plans": collect_notifications_about_expiring_plans,
}

_notifiers: dict[str, Callable[..., None]] = {
    "actions": notify_user_about_expiring_actions,
    "messages": notify_user_about_messages,
    "plans": notify_user_about_expiring_plans,
}

_tasks: dict[str, Any] = {
    "email": send_email,
}
