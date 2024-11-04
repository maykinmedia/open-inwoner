from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_yubin.models import Message
from freezegun import freeze_time

from open_inwoner.configurations.tasks import send_failed_mail_digest

from ..emails import inform_admins_about_failing_emails
from ..models import SiteConfiguration


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class DailyFailingEmailDigestTestCase(TestCase):
    def test_no_recipients_configured(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = []
        config.save()

        with freeze_time("2024-01-01T12:00:00"):
            message = Message()
            message.status = Message.STATUS_FAILED
            message.subject = "Some subject"
            message.to_address = "to@example.com"
            message.save()

        with freeze_time("2024-01-02T00:00:00"):
            inform_admins_about_failing_emails()

        self.assertEqual(len(mail.outbox), 0)

    def test_send_daily_failing_email_digest(self):
        config = SiteConfiguration.get_solo()
        config.recipients_email_digest = ["admin@localhost", "admin2@localhost"]
        config.save()

        with freeze_time("2023-12-31T12:00:00"):
            message = Message()
            message.status = Message.STATUS_FAILED
            message.subject = "Old message should not show up in email"
            message.to_address = "to@example.com"
            message.save()

        with freeze_time("2024-01-01T12:00:00"):
            message2 = Message()
            message2.status = Message.STATUS_SENT
            message2.subject = "Sent message should not show up in email"
            message2.to_address = "to@example.com"
            message2.save()

            message3 = Message()
            message3.status = Message.STATUS_FAILED
            message3.subject = "Should show up in email"
            message3.to_address = "to@example.com"
            message3.save()

        with freeze_time("2024-01-02T00:00:00"):
            inform_admins_about_failing_emails()

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(
            email.subject, "Gefaalde emails voor Open Inwoner Platform (2 januari 2024)"
        )
        self.assertEqual(email.to, ["admin@localhost", "admin2@localhost"])
        self.assertNotIn("Old message should not show up in email", email.body)
        self.assertNotIn("Sent message should not show up in email", email.body)
        self.assertIn("Should show up in email", email.body)
        self.assertIn("to@example.com", email.body)
        self.assertIn("1 januari 2024 13:00", email.body)

    @patch("open_inwoner.configurations.tasks.call_command")
    def test_command_called_when_task_triggered(self, mock_command):
        send_failed_mail_digest()

        mock_command.assert_called_once()
        self.assertEqual(mock_command.call_args.args, ("send_failed_mail_digest",))

    @patch(
        "open_inwoner.configurations.management.commands."
        "send_failed_mail_digest.inform_admins_about_failing_emails"
    )
    def test_entrypoint_called_when_command_called(self, mock):
        call_command("send_failed_mail_digest")

        mock.assert_called_once()
        self.assertEqual(mock.call_args.args, ())
