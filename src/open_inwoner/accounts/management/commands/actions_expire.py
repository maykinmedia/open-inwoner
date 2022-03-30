import logging
from datetime import date
from typing import List

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.urls import reverse

from mail_editor.helpers import find_template

from open_inwoner.accounts.models import Action, User

logger = logging.getLogger(__name__)


def build_absolute_url(path: str) -> str:
    domain = Site.objects.get_current().domain
    protocol = "https" if settings.IS_HTTPS else "http"
    return f"{protocol}://{domain}{path}"


class Command(BaseCommand):
    help = "Send emails about new messages to the users"

    def handle(self, *args, **options):
        today = date.today()
        user_ids = Action.objects.filter(end_date=today).values_list(
            "is_for_id", flat=True
        )
        receivers = User.objects.filter(is_active=True, pk__in=user_ids).distinct()

        for receiver in receivers:
            """send email to each user"""
            actions = Action.objects.filter(is_for=receiver, end_date=today)
            self.send_email(
                receiver=receiver,
                actions=actions,
            )

            logger.info(
                f"The email was send to the user {receiver} about {actions.count()} expiring actions"
            )

    def send_email(self, receiver: User, actions: List[Action]):
        actions_link = build_absolute_url(reverse("accounts:action_list"))
        template = find_template("expiring_action")
        context = {
            "actions": actions,
            "actions_link": actions_link,
        }

        return template.send_email([receiver.email], context)
