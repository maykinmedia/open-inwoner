from unittest.mock import patch

from django.test import TestCase, override_settings

from zgw_consumers.constants import APITypes
from zgw_consumers.models.services import Service

from notifications.constants import ProcessingStatus
from notifications.exceptions import (
    NotificationAlreadyProcessedError,
    NotificationRecordLockError,
    NotificationSkippedException,
)
from notifications.models import (
    NotificationRecord,
    NotificationsAPIConfig,
    Subscription,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.tasks import process_zaken_notification


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class ProcessZakenNotificationTaskTestCase(TestCase):
    """Tests for process_zaken_notification Celery task"""

    @classmethod
    def setUpTestData(cls):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
            oas="http://some-api-root/api/v1/schema/openapi.yaml",
        )
        cls.config = NotificationsAPIConfig.objects.create(
            notifications_api_service=service
        )
        cls.subscription = Subscription.objects.create(
            notifications_api_config=cls.config,
            callback_url="https://example.com/callback",
            client_id="test_client",
            secret="test_secret",
            channels=["zaken"],
        )

    def setUp(self):
        # Ensure notifications are enabled by default
        config = SiteConfiguration.get_solo()
        config.notifications_cases_enabled = True
        config.save()

    @patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
    def test_process_notification_success(self, mock_handle):
        """Test successful notification processing"""
        payload = {
            "kanaal": "zaken",
            "resource": "zaak",
            "resourceUrl": "http://example.com/zaak/1",
            "hoofdObject": "http://example.com/zaak/1",
            "actie": "create",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
        }
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload=payload,
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        process_zaken_notification(record.pk)

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(record.last_processed_at)
        mock_handle.assert_called_once()

    @patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
    def test_process_notification_when_disabled(self, mock_handle):
        """Test that notification processing is skipped when notifications are disabled"""
        # Disable notifications
        config = SiteConfiguration.get_solo()
        config.notifications_cases_enabled = False
        config.save()

        payload = {
            "kanaal": "zaken",
            "resource": "zaak",
            "resourceUrl": "http://example.com/zaak/1",
            "hoofdObject": "http://example.com/zaak/1",
            "actie": "create",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
        }
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload=payload,
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        # Task should raise NotificationSkippedException
        with self.assertRaises(NotificationSkippedException):
            process_zaken_notification(record.pk)

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.SKIPPED)
        self.assertIn("Case notifications are disabled", record.processing_output)
        self.assertIsNotNone(record.last_processed_at)
        mock_handle.assert_not_called()

    @patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
    def test_process_notification_handler_raises_exception(self, mock_handle):
        """Test that exceptions from handler are properly recorded"""
        mock_handle.side_effect = ValueError("Test error from handler")

        payload = {
            "kanaal": "zaken",
            "resource": "zaak",
            "resourceUrl": "http://example.com/zaak/1",
            "hoofdObject": "http://example.com/zaak/1",
            "actie": "create",
            "aanmaakdatum": "2023-01-11T15:09:59.116815Z",
        }
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload=payload,
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with self.assertRaises(ValueError):
            process_zaken_notification(record.pk)

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.FAILED)
        self.assertEqual(record.processing_error, "Test error from handler")
        self.assertIsNotNone(record.last_processed_at)

    def test_process_notification_record_does_not_exist(self):
        """Test handling of non-existent notification record"""
        with self.assertRaises(NotificationRecord.DoesNotExist):
            process_zaken_notification(99999)

    @patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
    def test_process_notification_already_processed(self, mock_handle):
        """Test that already processed records raise lock error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"kanaal": "zaken"},
            kanaal="zaken",
            status=ProcessingStatus.SUCCESS,  # Already processed
        )

        with self.assertRaises(NotificationAlreadyProcessedError) as cm:
            process_zaken_notification(record.pk)

        self.assertIn("already processed", str(cm.exception))
        mock_handle.assert_not_called()

    @patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
    def test_process_notification_already_locked(self, mock_handle):
        """Test that locked records raise lock error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"kanaal": "zaken"},
            kanaal="zaken",
            status=ProcessingStatus.PROCESSING,  # Currently being processed
        )

        with self.assertRaises(NotificationRecordLockError) as cm:
            process_zaken_notification(record.pk)

        self.assertIn("already locked or not pending", str(cm.exception))
        mock_handle.assert_not_called()

    @patch("open_inwoner.openzaak.tasks.handle_zaken_notification", autospec=True)
    def test_process_notification_invalid_payload(self, mock_handle):
        """Test that invalid payload structure causes failure"""
        # With JSONField, we can't store invalid JSON, but we can store
        # a payload that doesn't match the Notification schema
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"invalid": "structure"},  # Missing required Notification fields
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with self.assertRaises(
            TypeError
        ):  # Factory will raise TypeError for missing required args
            process_zaken_notification(record.pk)

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.FAILED)
        self.assertIn("missing", record.processing_error.lower())
