from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_yubin import send_mail as yubin_send_mail
from django_yubin.models import Log
from freezegun import freeze_time

from open_inwoner.configurations.tasks import send_failed_mail_digest

from ..models import SiteConfiguration


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class DailyFailingEmailDigestTestCase(TestCase):
    def test_no_recipients_configured(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = []
        config.save()

        with freeze_time("2024-01-01T12:00:00"):
            yubin_send_mail(
                subject="Some subject",
                from_email="from@example.com",
                recipient_list=["to@example.com"],
                message="test",
            )

        self.assertEqual(Log.objects.count(), 1)

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 0)

    def test_no_failing_emails_in_past_24_hours(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            yubin_send_mail(
                subject="Some subject",
                from_email="from@example.com",
                recipient_list=["to@example.com"],
                message="test",
            )

        self.assertEqual(Log.objects.count(), 1)

        with freeze_time("2024-01-02T00:00:00"):
            call_command("send_failed_mail_digest")

        self.assertEqual(len(mail.outbox), 0)

    def test_send_daily_failing_email_digest(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost", "admin2@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            yubin_send_mail(
                subject="Should not show up in email",
                from_email="from@example.com",
                recipient_list=["to@example.com"],
                message="test",
            )

        with freeze_time("2024-01-01T12:00:00"):
            yubin_send_mail(
                subject="Should show up in email",
                from_email="from@example.com",
                recipient_list=["to@example.com"],
                message="test",
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

    def test_task_triggers_sending_of_digest(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost"]
        config.save()

        with freeze_time("2024-01-01T12:00:00"):
            yubin_send_mail(
                subject="Should show up in email",
                from_email="from@example.com",
                recipient_list=["to@example.com"],
                message="test",
            )

        with freeze_time("2024-01-02T00:00:00"):
            send_failed_mail_digest.delay()

        self.assertEqual(len(mail.outbox), 1)

    # Due to Celery's eager task discovery, we have to mock the imported
    # call_command.
    @mock.patch("open_inwoner.configurations.tasks.call_command")
    def test_task_invokes_management_command(self, m):
        send_failed_mail_digest.delay()
        m.assert_called_once_with("send_failed_mail_digest")
