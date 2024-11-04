import logging

from django.db.models import Count
from django.urls import reverse

from mail_editor.helpers import find_template

from open_inwoner.accounts.models import Message, User
from open_inwoner.utils.url import build_absolute_url

logger = logging.getLogger(__name__)


def collect_notifications_about_messages() -> list[dict]:
    """
    Gather identifying data about users + their messages for notification

    Note:
        we store id's of users + messages on the `Notification` for
        reconstruction of the QuerySet when the notification is sent because
        the QuerySet cannot be JSON-serialized (needed for celery)
    """
    receivers = User.objects.filter(
        received_messages__seen=False,
        received_messages__sent=False,
        is_active=True,
        messages_notifications=True,
    ).distinct()

    notifications = [
        dict(
            receiver_id=receiver.pk,
            object_ids=list(
                Message.objects.filter(
                    receiver=receiver,
                    seen=False,
                    sent=False,
                ).values_list("id", flat=True)
            ),
            object_type=str(Message),
        )
        for receiver in receivers
    ]

    return notifications


def notify_user_about_messages(
    receiver_id: int, object_ids: list[int], channel: str
) -> None:
    send = _channels[channel]

    send(receiver_id=receiver_id, message_ids=object_ids)


def _send_email(receiver_id: int, message_ids: list[int]) -> None:
    inbox_url = build_absolute_url(reverse("inbox:index"))
    template = find_template("new_messages")

    receiver = User.objects.get(pk=receiver_id)
    messages = Message.objects.filter(pk__in=message_ids)

    total_messages = messages.count()
    total_senders = messages.aggregate(total_senders=Count("sender", distinct=True))[
        "total_senders"
    ]

    context = {
        "total_messages": total_messages,
        "total_senders": total_senders,
        "inbox_link": inbox_url,
    }

    template.send_email([receiver.email], context)

    messages.update(sent=True)

    logger.info(
        f"The email was sent to the user {receiver} about {total_messages} new messages"
    )


_channels = {
    "email": _send_email,
}
