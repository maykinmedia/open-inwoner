import logging
from datetime import date

from django.urls import reverse

from mail_editor.helpers import find_template

from open_inwoner.accounts.choices import StatusChoices
from open_inwoner.accounts.models import Action, User
from open_inwoner.utils.url import build_absolute_url

logger = logging.getLogger(__name__)


def collect_notifications_about_expiring_actions() -> list[dict]:
    """
    Gather identifying data about users + their expiring actions for notification

    Note:
        we store id's of users + expiring actions in a dict for transfer and
        reconstruction of the QuerySet when the notification is sent because
        the QuerySet cannot be JSON-serialized (needed for celery)
    """
    today = date.today()
    receivers = User.objects.filter(
        is_active=True,
        plans_notifications=True,
        actions__end_date=today,
        actions__status__in=[StatusChoices.open, StatusChoices.approval],
    ).distinct()

    notifications = [
        dict(
            receiver_id=receiver.pk,
            object_ids=list(
                Action.objects.filter(
                    is_for=receiver,
                    end_date=today,
                ).values_list("id", flat=True)
            ),
            object_type=str(Action),
        )
        for receiver in receivers
    ]

    return notifications


def notify_user_about_expiring_actions(
    receiver_id: int, object_ids: list[int], channel: str
) -> None:
    func = _channels[channel]

    func(receiver_id=receiver_id, action_ids=object_ids)


def _send_email(receiver_id: int, action_ids: list[int]) -> None:
    actions_link = build_absolute_url(reverse("profile:action_list"))
    template = find_template("expiring_action")

    receiver = User.objects.get(pk=receiver_id)
    actions = Action.objects.filter(pk__in=action_ids)

    context = {
        "actions": actions,
        "actions_link": actions_link,
    }

    template.send_email([receiver.email], context)

    logger.info(
        f"The email was sent to the user {receiver} about {actions.count()} expiring actions"
    )


_channels = {
    "email": _send_email,
}
