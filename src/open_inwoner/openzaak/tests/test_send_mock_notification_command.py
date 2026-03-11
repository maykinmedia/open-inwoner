from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from notifications.constants import ProcessingStatus
from notifications.models import NotificationRecord

from .factories import SubscriptionFactory


class SendMockNotificationCommandTestCase(TestCase):
    def setUp(self):
        self.subscription = SubscriptionFactory.create(
            client_id="test-client",
            secret="test-secret",
            channels=["zaken"],
        )

    def test_default_sends_five_valid_and_two_malformed(self):
        call_command("send_mock_notification", stdout=StringIO())

        self.assertEqual(NotificationRecord.objects.count(), 7)
        self.assertEqual(
            NotificationRecord.objects.filter(status=ProcessingStatus.PENDING).count(),
            5,
        )
        self.assertEqual(
            NotificationRecord.objects.filter(status=ProcessingStatus.FAILED).count(), 2
        )

    def test_no_malformed_sends_only_valid(self):
        call_command("send_mock_notification", no_malformed=True, stdout=StringIO())

        self.assertEqual(NotificationRecord.objects.count(), 5)
        self.assertEqual(
            NotificationRecord.objects.filter(status=ProcessingStatus.PENDING).count(),
            5,
        )
        self.assertFalse(
            NotificationRecord.objects.filter(status=ProcessingStatus.FAILED).exists()
        )

    def test_custom_count(self):
        call_command("send_mock_notification", count=3, stdout=StringIO())

        self.assertEqual(
            NotificationRecord.objects.filter(status=ProcessingStatus.PENDING).count(),
            3,
        )
        self.assertEqual(
            NotificationRecord.objects.filter(status=ProcessingStatus.FAILED).count(), 2
        )

    def test_specific_subscription(self):
        other = SubscriptionFactory.create(channels=["zaken"])

        call_command(
            "send_mock_notification",
            subscription=self.subscription.pk,
            no_malformed=True,
            stdout=StringIO(),
        )

        self.assertEqual(
            NotificationRecord.objects.filter(subscription=self.subscription).count(), 5
        )
        self.assertFalse(NotificationRecord.objects.filter(subscription=other).exists())

    def test_no_subscription_raises_error(self):
        self.subscription.delete()

        with self.assertRaises(CommandError):
            call_command("send_mock_notification", stdout=StringIO())

    def test_invalid_subscription_pk_raises_error(self):
        with self.assertRaises(CommandError):
            call_command(
                "send_mock_notification", subscription=99999, stdout=StringIO()
            )

    def test_output_reports_accepted_and_rejected(self):
        out = StringIO()
        call_command("send_mock_notification", stdout=out)

        output = out.getvalue()
        self.assertIn("204 Accepted", output)
        self.assertIn("malformed", output)
