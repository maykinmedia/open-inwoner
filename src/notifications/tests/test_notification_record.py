import uuid

from django.test import TestCase, TransactionTestCase

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


class NotificationRecordLockManagerTestCase(TransactionTestCase):
    """
    Tests for NotificationRecordManager.lock_for_processing() context manager.

    Uses TransactionTestCase because we need to test concurrent behavior with
    real database transactions.
    """

    def setUp(self):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
        )
        self.config = NotificationsAPIConfig.objects.create(
            notifications_api_service=service
        )
        self.subscription = Subscription.objects.create(
            notifications_api_config=self.config,
            callback_url="https://example.com/callback",
            client_id="test_client",
            secret="test_secret",
            channels=["zaken"],
        )

    def test_lock_for_processing_with_pk_success(self):
        """Test successful lock acquisition using primary key"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with NotificationRecord.objects.lock_for_processing(record.pk) as locked_record:
            # Should get the record in PROCESSING status with process_started_at set
            self.assertEqual(locked_record.pk, record.pk)
            self.assertEqual(locked_record.status, ProcessingStatus.PROCESSING)
            self.assertIsNotNone(locked_record.process_started_at)

        # After context manager, should be SUCCESS
        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(record.last_processed_at)
        self.assertIsNotNone(record.process_started_at)

    def test_lock_for_processing_with_instance_success(self):
        """Test successful lock acquisition using NotificationRecord instance"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with NotificationRecord.objects.lock_for_processing(record) as locked_record:
            # Should get the record in PROCESSING status with process_started_at set
            self.assertEqual(locked_record.pk, record.pk)
            self.assertEqual(locked_record.status, ProcessingStatus.PROCESSING)
            self.assertIsNotNone(locked_record.process_started_at)

        # After context manager, should be SUCCESS
        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.SUCCESS)
        self.assertIsNotNone(record.last_processed_at)
        self.assertIsNotNone(record.process_started_at)

    def test_lock_for_processing_already_locked(self):
        """Test that locking an already locked record raises error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PROCESSING,
        )

        with self.assertRaises(NotificationRecordLockError) as cm:
            with NotificationRecord.objects.lock_for_processing(record.pk):
                pass

        self.assertIn("already locked or not pending", str(cm.exception))

    def test_lock_for_processing_already_processed_success(self):
        """Test that locking a SUCCESS record raises error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.SUCCESS,
        )

        with self.assertRaises(NotificationAlreadyProcessedError) as cm:
            with NotificationRecord.objects.lock_for_processing(record.pk):
                pass

        self.assertIn("already processed with status: success", str(cm.exception))

    def test_lock_for_processing_already_processed_failed(self):
        """Test that locking a FAILED record raises error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.FAILED,
        )

        with self.assertRaises(NotificationAlreadyProcessedError) as cm:
            with NotificationRecord.objects.lock_for_processing(record.pk):
                pass

        self.assertIn("already processed with status: failed", str(cm.exception))

    def test_lock_for_processing_already_skipped(self):
        """Test that locking a SKIPPED record raises error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.SKIPPED,
        )

        with self.assertRaises(NotificationAlreadyProcessedError) as cm:
            with NotificationRecord.objects.lock_for_processing(record.pk):
                pass

        self.assertIn("already processed with status: skipped", str(cm.exception))

    def test_lock_for_processing_already_processed_with_instance(self):
        """Test that passing a stale instance for a final-state record raises the correct error"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )
        # Simulate a stale instance: mutate in DB but don't refresh the local object
        NotificationRecord.objects.filter(pk=record.pk).update(
            status=ProcessingStatus.SUCCESS
        )

        with self.assertRaises(NotificationAlreadyProcessedError) as cm:
            with NotificationRecord.objects.lock_for_processing(record):
                pass

        self.assertIn("already processed with status: success", str(cm.exception))

    def test_lock_for_processing_exception_sets_failed(self):
        """Test that exception during processing sets status to FAILED with error message"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with self.assertRaises(RuntimeError):
            with NotificationRecord.objects.lock_for_processing(record.pk):
                raise RuntimeError("Test error message")

        # Should be set to FAILED with error message
        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.FAILED)
        self.assertEqual(record.processing_error, "Test error message")
        self.assertIsNotNone(record.last_processed_at)
        self.assertIsNotNone(record.process_started_at)

    def test_lock_for_processing_skipped_exception_sets_skipped(self):
        """Test that NotificationSkippedException sets status to SKIPPED"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with self.assertRaises(NotificationSkippedException):
            with NotificationRecord.objects.lock_for_processing(record.pk):
                raise NotificationSkippedException("Notifications disabled")

        # Should be set to SKIPPED
        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.SKIPPED)
        self.assertEqual(record.processing_error, "Notifications disabled")
        self.assertIsNotNone(record.last_processed_at)
        self.assertIsNotNone(record.process_started_at)

    def test_lock_for_processing_record_does_not_exist(self):
        """Test that locking non-existent record raises DoesNotExist"""
        with self.assertRaises(NotificationRecord.DoesNotExist):
            with NotificationRecord.objects.lock_for_processing(uuid.uuid4()):
                pass


class NotificationRecordResetForRetryTestCase(TestCase):
    """Tests for NotificationRecord.reset_for_retry() method"""

    @classmethod
    def setUpTestData(cls):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
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

    def test_reset_for_retry_from_failed(self):
        """Test resetting a FAILED record to PENDING"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.FAILED,
            processing_error="Previous error",
        )

        record.reset_for_retry()

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.PENDING)
        self.assertEqual(record.processing_error, "")

    def test_reset_for_retry_from_success(self):
        """Test resetting a SUCCESS record to PENDING"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.SUCCESS,
        )

        record.reset_for_retry()

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.PENDING)
        self.assertEqual(record.processing_error, "")

    def test_reset_for_retry_from_skipped(self):
        """Test resetting a SKIPPED record to PENDING"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.SKIPPED,
            processing_error="Previously skipped",
        )

        record.reset_for_retry()

        record.refresh_from_db()
        self.assertEqual(record.status, ProcessingStatus.PENDING)
        self.assertEqual(record.processing_error, "")

    def test_reset_for_retry_from_pending_raises_error(self):
        """Test that resetting a PENDING record raises ValueError"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PENDING,
        )

        with self.assertRaises(ValueError) as cm:
            record.reset_for_retry()

        self.assertIn("Cannot reset record with status pending", str(cm.exception))
        self.assertIn("FAILED, SUCCESS, or SKIPPED", str(cm.exception))

    def test_reset_for_retry_from_processing_raises_error(self):
        """Test that resetting a PROCESSING record raises ValueError"""
        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            kanaal="zaken",
            status=ProcessingStatus.PROCESSING,
        )

        with self.assertRaises(ValueError) as cm:
            record.reset_for_retry()

        self.assertIn("Cannot reset record with status processing", str(cm.exception))
        self.assertIn("FAILED, SUCCESS, or SKIPPED", str(cm.exception))
