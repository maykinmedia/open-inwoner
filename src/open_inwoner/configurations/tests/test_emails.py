import uuid

from django.core import mail
from django.core.mail import EmailMessage
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time
from mailer.models import (
    PRIORITY_MEDIUM,
    RESULT_FAILURE,
    RESULT_SUCCESS,
    MessageLog,
    email_to_db,
)

from ..models import SiteConfiguration


def make_message_log(to, subject, result):
    """
    hand-craft a minimal version of what django-mailer stores as log
    """
    assert isinstance(to, list)
    data = EmailMessage(subject=subject, to=to, from_email="from@example.com")

    log = MessageLog.objects.create(
        message_id=f"message_id-{uuid.uuid4()}",
        # it wraps pickle and base64
        message_data=email_to_db(data),
        result=result,
        when_added=timezone.now(),
        priority=PRIORITY_MEDIUM,
    )
    return log


class DailyFailingEmailDigestTestCase(TestCase):
    def test_no_recipients_configured(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = []
        config.save()

        with freeze_time("2024-01-01T12:00:00"):
            make_message_log(["to@example.com"], "failed message", RESULT_FAILURE)

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 0)

    def test_no_failing_emails_in_past_24_hours(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            make_message_log(["to@example.com"], "failed message", RESULT_FAILURE)

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 0)

    def test_send_daily_failing_email_digest(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost", "admin2@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            # out of date range
            make_message_log(
                ["to@example.com"], "Should not show up in email", RESULT_SUCCESS
            )

        with freeze_time("2024-01-01T12:00:00"):
            make_message_log(
                ["to@example.com"], "Should show up in email", RESULT_FAILURE
            )
            # in range but success
            make_message_log(
                ["to@example.com"], "Should not show up in email", RESULT_SUCCESS
            )

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(
            email.subject, "Gefaalde emails voor Open Inwoner Platform (2 januari 2024)"
        )
        self.assertEqual(email.to, ["admin@localhost", "admin2@localhost"])
        self.assertNotIn("Should not show up in email", email.body)
        self.assertIn("Should show up in email", email.body)
        self.assertIn("to@example.com", email.body)
        self.assertIn("1 januari 2024 13:00", email.body)
