import logging
from datetime import date
from typing import List

from django.core.management.base import BaseCommand
from django.urls import reverse

from mail_editor.helpers import find_template

from open_inwoner.accounts.models import Action, User
from open_inwoner.utils.url import build_absolute_url

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send emails about expiring actions to the users"

    def handle(self, *args, **options):
        today = date.today()
        user_ids = Action.objects.filter(end_date=today).values_list(
            "is_for_id", flat=True
        )
        receivers = User.objects.filter(
            is_active=True, pk__in=user_ids, plans_notifications=True
        ).distinct()

        for receiver in receivers:
            """send email to each user"""
            actions = Action.objects.filter(is_for=receiver, end_date=today)
            self.send_email(
                receiver=receiver,
                actions=actions,
            )

            logger.info(
                f"The email was sent to the user {receiver} about {actions.count()} expiring actions"
            )

    def send_email(self, receiver: User, actions: List[Action]):
        actions_link = build_absolute_url(reverse("profile:action_list"))
        template = find_template("expiring_action")
        context = {
            "actions": actions,
            "actions_link": actions_link,
        }

        return template.send_email([receiver.email], context)
