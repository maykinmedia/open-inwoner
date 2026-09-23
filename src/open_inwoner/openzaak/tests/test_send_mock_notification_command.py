from datetime import date, datetime
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from notifications.constants import ProcessingStatus
from notifications.models import NotificationRecord
from open_inwoner.openzaak.api_models import Status, Zaak

from .factories import SubscriptionFactory


class SendMockNotificationCommandTestCase(TestCase):
    def setUp(self):
        self.subscription = SubscriptionFactory.create(
            client_id="test-client",
            secret="test-secret",
            channels=["zaken"],
        )

        # The command posts through the real webhook, which hands the record to a
        # Celery worker. These tests are about what the command sends and what the
        # webhook accepts, so the dispatch is stubbed out: without it they need a
        # live broker to leave records PENDING, and with CELERY_TASK_ALWAYS_EAGER
        # the task runs inline and moves them straight past PENDING instead.
        patcher = patch("open_inwoner.openzaak.api.views.process_zaken_notification")
        self.mock_task = patcher.start()
        self.addCleanup(patcher.stop)

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

    def test_resource_status_with_explicit_urls_skips_discovery(self):
        call_command(
            "send_mock_notification",
            resource="status",
            zaak_url="https://zaken.example.com/api/v1/zaken/1",
            status_url="https://zaken.example.com/api/v1/statussen/1",
            no_malformed=True,
            count=1,
            stdout=StringIO(),
        )

        record = NotificationRecord.objects.get()
        self.assertEqual(record.payload["resource"], "status")
        self.assertEqual(
            record.payload["hoofdObject"], "https://zaken.example.com/api/v1/zaken/1"
        )
        self.assertEqual(
            record.payload["resourceUrl"],
            "https://zaken.example.com/api/v1/statussen/1",
        )
        self.assertEqual(record.payload["actie"], "create")

    def test_status_url_without_zaak_url_raises_error(self):
        with self.assertRaises(CommandError):
            call_command(
                "send_mock_notification",
                resource="status",
                status_url="https://zaken.example.com/api/v1/statussen/1",
                stdout=StringIO(),
            )

    def test_resource_status_without_urls_requires_zgw_config(self):
        with self.assertRaises(CommandError):
            call_command("send_mock_notification", resource="status", stdout=StringIO())

    def test_resource_zaakinformatieobject_requires_urls(self):
        with self.assertRaises(CommandError):
            call_command(
                "send_mock_notification",
                resource="zaakinformatieobject",
                stdout=StringIO(),
            )

    def test_resource_zaakinformatieobject_fetches_kenmerken_from_zaak(self):
        zaak = Zaak(
            url="https://zaken.example.com/api/v1/zaken/1",
            identificatie="ZAAK-1",
            bronorganisatie="123443210",
            omschrijving="Test zaak",
            zaaktype="https://catalogi.example.com/api/v1/zaaktypen/1",
            registratiedatum=date(2024, 1, 1),
            startdatum=date(2024, 1, 1),
            vertrouwelijkheidaanduiding="openbaar",
            status=None,
        )
        mock_client = MagicMock()
        mock_client.fetch_zaak_by_url_no_cache.return_value = zaak

        with patch(
            "open_inwoner.openzaak.management.commands.send_mock_notification"
            ".build_zaken_clients",
            return_value=[mock_client],
        ):
            call_command(
                "send_mock_notification",
                resource="zaakinformatieobject",
                zaak_url=zaak.url,
                informatieobject_url=(
                    "https://documenten.example.com/api/v1/"
                    "enkelvoudiginformatieobjecten/1"
                ),
                no_malformed=True,
                count=1,
                stdout=StringIO(),
            )

        record = NotificationRecord.objects.get()
        self.assertEqual(record.payload["resource"], "zaakinformatieobject")
        self.assertEqual(record.payload["hoofdObject"], zaak.url)
        self.assertEqual(
            record.payload["resourceUrl"],
            "https://documenten.example.com/api/v1/enkelvoudiginformatieobjecten/1",
        )
        self.assertEqual(record.payload["kenmerken"]["bronorganisatie"], "123443210")
        self.assertEqual(
            record.payload["kenmerken"]["zaaktype"],
            "https://catalogi.example.com/api/v1/zaaktypen/1",
        )

    def test_resource_status_auto_discovers_latest_status(self):
        zaak = Zaak(
            url="https://zaken.example.com/api/v1/zaken/1",
            identificatie="ZAAK-1",
            bronorganisatie="123443210",
            omschrijving="Test zaak",
            zaaktype="https://catalogi.example.com/api/v1/zaaktypen/1",
            registratiedatum=date(2024, 1, 1),
            startdatum=date(2024, 1, 1),
            vertrouwelijkheidaanduiding="openbaar",
            status=None,
        )
        older = Status(
            url="https://zaken.example.com/api/v1/statussen/1",
            zaak=zaak.url,
            statustype="https://catalogi.example.com/api/v1/statustypen/1",
            datum_status_gezet=timezone.make_aware(datetime(2024, 1, 1)),
        )
        newer = Status(
            url="https://zaken.example.com/api/v1/statussen/2",
            zaak=zaak.url,
            statustype="https://catalogi.example.com/api/v1/statustypen/2",
            datum_status_gezet=timezone.make_aware(datetime(2024, 2, 1)),
        )
        mock_client = MagicMock()
        mock_client.fetch_zaken_by_bsn.return_value = [zaak]
        mock_client.fetch_status_history.return_value = [older, newer]

        with patch(
            "open_inwoner.openzaak.management.commands.send_mock_notification"
            ".build_zaken_clients",
            return_value=[mock_client],
        ):
            call_command(
                "send_mock_notification",
                resource="status",
                bsn="111222333",
                no_malformed=True,
                count=1,
                stdout=StringIO(),
            )

        mock_client.fetch_zaken_by_bsn.assert_called_once_with("111222333")
        record = NotificationRecord.objects.get()
        self.assertEqual(record.payload["resourceUrl"], newer.url)
        self.assertEqual(record.payload["hoofdObject"], zaak.url)

    def test_resource_status_skips_zaken_with_only_an_initial_status(self):
        """
        A zaak with a single status is still on its initial status, and Open
        Inwoner's handler ignores a notification for it -- auto-discovery
        should skip straight past such zaken instead of picking one that
        would silently produce nothing.
        """

        def make_zaak(n):
            return Zaak(
                url=f"https://zaken.example.com/api/v1/zaken/{n}",
                identificatie=f"ZAAK-{n}",
                bronorganisatie="123443210",
                omschrijving="Test zaak",
                zaaktype="https://catalogi.example.com/api/v1/zaaktypen/1",
                registratiedatum=date(2024, 1, 1),
                startdatum=date(2024, 1, 1),
                vertrouwelijkheidaanduiding="openbaar",
                status=None,
            )

        def make_status(n):
            return Status(
                url=f"https://zaken.example.com/api/v1/statussen/{n}",
                zaak=f"https://zaken.example.com/api/v1/zaken/{n}",
                statustype=f"https://catalogi.example.com/api/v1/statustypen/{n}",
                datum_status_gezet=timezone.make_aware(datetime(2024, 1, n)),
            )

        initial_only = make_zaak(1)
        has_history = make_zaak(2)
        second_status = make_status(2)

        mock_client = MagicMock()
        mock_client.fetch_zaken_by_bsn.return_value = [initial_only, has_history]
        mock_client.fetch_status_history.side_effect = lambda zaak_url: (
            [make_status(1)]
            if zaak_url == initial_only.url
            else [make_status(1), second_status]
        )

        with patch(
            "open_inwoner.openzaak.management.commands.send_mock_notification"
            ".build_zaken_clients",
            return_value=[mock_client],
        ):
            call_command(
                "send_mock_notification",
                resource="status",
                bsn="111222333",
                no_malformed=True,
                count=1,
                stdout=StringIO(),
            )

        record = NotificationRecord.objects.get()
        self.assertEqual(record.payload["hoofdObject"], has_history.url)
        self.assertEqual(record.payload["resourceUrl"], second_status.url)

    def test_resource_status_raises_when_no_zaak_has_status_history(self):
        zaak = Zaak(
            url="https://zaken.example.com/api/v1/zaken/1",
            identificatie="ZAAK-1",
            bronorganisatie="123443210",
            omschrijving="Test zaak",
            zaaktype="https://catalogi.example.com/api/v1/zaaktypen/1",
            registratiedatum=date(2024, 1, 1),
            startdatum=date(2024, 1, 1),
            vertrouwelijkheidaanduiding="openbaar",
            status=None,
        )
        only_status = Status(
            url="https://zaken.example.com/api/v1/statussen/1",
            zaak=zaak.url,
            statustype="https://catalogi.example.com/api/v1/statustypen/1",
            datum_status_gezet=timezone.make_aware(datetime(2024, 1, 1)),
        )
        mock_client = MagicMock()
        mock_client.fetch_zaken_by_bsn.return_value = [zaak]
        mock_client.fetch_status_history.return_value = [only_status]

        with patch(
            "open_inwoner.openzaak.management.commands.send_mock_notification"
            ".build_zaken_clients",
            return_value=[mock_client],
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "send_mock_notification",
                    resource="status",
                    bsn="111222333",
                    stdout=StringIO(),
                )
