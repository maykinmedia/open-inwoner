import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from mail_editor.helpers import find_template

from open_inwoner.accounts.models import Message, User

logger = logging.getLogger(__name__)


def build_absolute_url(path: str) -> str:
    domain = Site.objects.get_current().domain
    protocol = "https" if settings.IS_HTTPS else "http"
    return f"{protocol}://{domain}{path}"


class Command(BaseCommand):
    help = "Send emails about new messages to the users"

    def handle(self, *args, **options):
        oldest_message_date = timezone.now() - timedelta(
            minutes=settings.NEW_MESSAGE_INTERVAL_MINUTES
        )

        receivers = User.objects.filter(
            received_messages__seen=False,
            received_messages__sent=False,
            received_messages__created_on__gte=oldest_message_date,
            is_active=True,
        ).distinct()

        for receiver in receivers:
            """send email to each user"""
            messages_to_update = Message.objects.filter(
                receiver=receiver,
                seen=False,
                sent=False,
                created_on__gte=oldest_message_date,
            )
            total_senders = messages_to_update.aggregate(
                total_senders=Count("sender", distinct=True)
            )["total_senders"]
            total_messages = messages_to_update.count()
            self.send_email(
                receiver=receiver,
                total_senders=total_senders,
                total_messages=total_messages,
            )

            """update messages"""
            messages_to_update.update(sent=True)

            logger.info(
                f"The email was send to the user {receiver} about {total_messages} new messages"
            )

    def send_email(self, receiver: User, total_senders: int, total_messages: int):
        inbox_url = build_absolute_url(reverse("accounts:inbox"))
        template = find_template("new_messages")
        context = {
            "total_messages": total_messages,
            "total_senders": total_senders,
            "inbox_link": inbox_url,
        }

        return template.send_email([receiver.email], context)
