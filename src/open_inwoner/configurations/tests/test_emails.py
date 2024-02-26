from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from django_yubin.constants import RESULT_FAILED
from django_yubin.models import Log, Message
from freezegun import freeze_time

from ..models import SiteConfiguration


class DailyFailingEmailDigestTestCase(TestCase):
    def test_no_recipients_configured(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = []
        config.save()

        with freeze_time("2024-01-01T12:00:00"):
            message = Message.objects.create(
                subject="Some subject",
                from_address="from@example.com",
                to_address="to@example.com",
                encoded_message="foo",
            )
            Log.objects.create(
                message=message, result=RESULT_FAILED, log_message="Some "
            )

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 0)

    def test_no_failing_emails_in_past_24_hours(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            message = Message.objects.create(
                subject="Some subject",
                from_address="from@example.com",
                to_address="to@example.com",
                encoded_message="foo",
            )
            Log.objects.create(
                message=message, result=RESULT_FAILED, log_message="Some msg"
            )

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 0)

    def test_send_daily_failing_email_digest(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost", "admin2@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            message = Message.objects.create(
                subject="Should not show up in email",
                from_address="from@example.com",
                to_address="to@example.com",
                encoded_message="foo",
            )
            Log.objects.create(
                message=message, result=RESULT_FAILED, log_message="Some msg"
            )

        with freeze_time("2024-01-01T12:00:00"):
            message = Message.objects.create(
                subject="Should show up in email",
                from_address="from@example.com",
                to_address="to@example.com",
                encoded_message="bar",
            )
            Log.objects.create(
                message=message, result=RESULT_FAILED, log_message="Some msg"
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
