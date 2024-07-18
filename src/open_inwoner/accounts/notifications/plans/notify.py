import logging
from datetime import date

from django.db.models.query import Q
from django.urls import reverse

from mail_editor.helpers import find_template

from open_inwoner.accounts.models import User
from open_inwoner.plans.models import Plan
from open_inwoner.userfeed import hooks as userfeed_hooks
from open_inwoner.utils.url import build_absolute_url

logger = logging.getLogger(__name__)


def collect_notifications_about_expiring_plans() -> list[dict]:
    """
    Gather identifying data about users + their expiring plans for notification

    Note:
        we store id's of users + expiring plans on the `Notification` for
        reconstruction of the QuerySet when the notification is sent because
        the QuerySet cannot be JSON-serialized (needed for celery)
    """
    today = date.today()

    # receivers are users who:
    # created or are otherwise associated with a plan that ends today and
    # are active and have notifications enabled
    receivers = (
        User.objects.filter(
            Q(id__in=Plan.objects.filter(end_date=today).values_list("created_by__id"))
            | Q(
                id__in=Plan.objects.filter(end_date=today).values_list(
                    "plan_contacts__id"
                )
            )
        )
        .filter(
            is_active=True,
            plans_notifications=True,
        )
        .distinct()
    )

    notifications = [
        dict(
            receiver_id=receiver.pk,
            object_ids=list(
                Plan.objects.filter(end_date=today)
                .filter(Q(created_by=receiver) | Q(plan_contacts=receiver))
                .values_list("id", flat=True),
            ),
            object_type=str(Plan),
        )
        for receiver in receivers
    ]

    return notifications


def notify_user_about_expiring_plans(
    receiver_id: int, object_ids: list[int], channel: str
) -> None:

    send = _channels[channel]

    send(receiver_id=receiver_id, plan_ids=object_ids)


def _send_email(receiver_id: int, plan_ids: list[int]) -> None:
    plan_list_link = build_absolute_url(reverse("collaborate:plan_list"))
    template = find_template("expiring_plan")

    receiver = User.objects.get(pk=receiver_id)
    receiver = User.objects.get(pk=receiver_id)
    plans = Plan.objects.filter(pk__in=plan_ids)

    for plan in plans:
        userfeed_hooks.plan_expiring(receiver, plan)

    context = {
        "plans": plans,
        "plan_list_link": plan_list_link,
    }

    template.send_email([receiver.email], context)

    logger.info(
        f"The email was sent to the user {receiver} about {plans.count()} expiring plans"
    )


_channels = {
    "email": _send_email,
}
