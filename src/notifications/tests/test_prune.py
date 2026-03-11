from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from zgw_consumers.constants import APITypes
from zgw_consumers.models.services import Service

from notifications.constants import ProcessingStatus
from notifications.models import (
    NotificationProcessingConfig,
    NotificationRecord,
    NotificationsAPIConfig,
    Subscription,
)


class PruneOldRecordsTestCase(TransactionTestCase):
    """Tests for NotificationRecordManager.prune_old_records() method."""

    def setUp(self):
        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
            oas="http://some-api-root/api/v1/schema/openapi.yaml",
        )
        config = NotificationsAPIConfig.objects.create(
            notifications_api_service=service
        )
        self.subscription = Subscription.objects.create(
            notifications_api_config=config,
            callback_url="https://example.com/callback",
            client_id="test_client",
            secret="test_secret",
            channels=["zaken"],
        )

    def test_prune_old_records_basic(self):
        """Test basic pruning of old records."""
        now = timezone.now()
        old_date = now - timedelta(days=31)

        # Create old records in final states
        old_success = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SUCCESS,
            last_processed_at=old_date,
        )
        old_failed = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.FAILED,
            last_processed_at=old_date,
        )
        old_skipped = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SKIPPED,
            last_processed_at=old_date,
        )

        # Create recent records - should not be deleted
        recent = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SUCCESS,
            last_processed_at=now,
        )

        # Create old pending record - should not be deleted
        old_pending = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PENDING,
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30, dry_run=False
        )

        self.assertEqual(result.total_count, 3)
        self.assertEqual(result.retention_days, 30)
        self.assertTrue(result.deleted)
        self.assertIsNone(result.stuck_processing_retention_days)
        self.assertIsNone(result.stuck_processing_cutoff_date)
        self.assertIn("success", result.breakdown_by_status)
        self.assertIn("failed", result.breakdown_by_status)
        self.assertIn("skipped", result.breakdown_by_status)

        self.assertFalse(NotificationRecord.objects.filter(pk=old_success.pk).exists())
        self.assertFalse(NotificationRecord.objects.filter(pk=old_failed.pk).exists())
        self.assertFalse(NotificationRecord.objects.filter(pk=old_skipped.pk).exists())
        self.assertTrue(NotificationRecord.objects.filter(pk=recent.pk).exists())
        self.assertTrue(NotificationRecord.objects.filter(pk=old_pending.pk).exists())

    def test_prune_old_records_dry_run(self):
        """Test dry run mode doesn't delete records."""
        now = timezone.now()
        old_date = now - timedelta(days=31)

        old_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SUCCESS,
            last_processed_at=old_date,
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30, dry_run=True
        )

        self.assertEqual(result.total_count, 1)
        self.assertFalse(result.deleted)
        self.assertTrue(NotificationRecord.objects.filter(pk=old_record.pk).exists())

    def test_prune_old_records_no_records(self):
        """Test pruning when no old records exist."""
        result = NotificationRecord.objects.prune_old_records(
            retention_days=30, dry_run=False
        )

        self.assertEqual(result.total_count, 0)
        self.assertFalse(result.deleted)
        self.assertEqual(result.breakdown_by_status, {})
        self.assertFalse(result.has_records)

    def test_prune_old_records_breakdown(self):
        """Test status breakdown is accurate."""
        now = timezone.now()
        old_date = now - timedelta(days=31)

        for _ in range(3):
            NotificationRecord.objects.create(
                subscription=self.subscription,
                payload={"test": "data"},
                status=ProcessingStatus.SUCCESS,
                last_processed_at=old_date,
            )

        for _ in range(2):
            NotificationRecord.objects.create(
                subscription=self.subscription,
                payload={"test": "data"},
                status=ProcessingStatus.FAILED,
                last_processed_at=old_date,
            )

        NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SKIPPED,
            last_processed_at=old_date,
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30, dry_run=False
        )

        self.assertEqual(result.total_count, 6)
        self.assertEqual(result.breakdown_by_status["success"], 3)
        self.assertEqual(result.breakdown_by_status["failed"], 2)
        self.assertEqual(result.breakdown_by_status["skipped"], 1)

    def test_prune_old_records_processing_not_deleted_without_config(self):
        """Test that PROCESSING records are not deleted when stuck_processing_retention_days is not set."""
        now = timezone.now()
        old_date = now - timedelta(days=31)

        processing_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PROCESSING,
            process_started_at=old_date,
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30, dry_run=False
        )

        self.assertEqual(result.total_count, 0)
        self.assertTrue(
            NotificationRecord.objects.filter(pk=processing_record.pk).exists()
        )

    def test_prune_old_records_stuck_processing_deleted(self):
        """Test that old PROCESSING records are deleted when stuck_processing_retention_days is set."""
        now = timezone.now()
        old_date = now - timedelta(days=8)

        stuck_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PROCESSING,
            process_started_at=old_date,
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30,
            stuck_processing_retention_days=7,
            dry_run=False,
        )

        self.assertEqual(result.total_count, 1)
        self.assertTrue(result.deleted)
        self.assertEqual(result.breakdown_by_status.get("processing"), 1)
        self.assertIsNotNone(result.stuck_processing_cutoff_date)
        self.assertFalse(NotificationRecord.objects.filter(pk=stuck_record.pk).exists())

    def test_prune_old_records_recent_processing_not_deleted(self):
        """Test that recent PROCESSING records are not deleted even with stuck_processing_retention_days set."""
        recent_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PROCESSING,
            process_started_at=timezone.now(),
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30,
            stuck_processing_retention_days=7,
            dry_run=False,
        )

        self.assertEqual(result.total_count, 0)
        self.assertTrue(NotificationRecord.objects.filter(pk=recent_record.pk).exists())

    def test_prune_old_records_stuck_processing_uses_separate_cutoff(self):
        """Test that stuck PROCESSING and terminal records use their independent cutoff dates."""
        now = timezone.now()

        # Record that's 20 days old: old enough for stuck processing (7d) but not for terminal (30d)
        stuck_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PROCESSING,
            process_started_at=now - timedelta(days=20),
        )
        # Terminal record that's 20 days old: NOT old enough for 30d terminal retention
        recent_terminal = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.FAILED,
            last_processed_at=now - timedelta(days=20),
        )

        result = NotificationRecord.objects.prune_old_records(
            retention_days=30,
            stuck_processing_retention_days=7,
            dry_run=False,
        )

        self.assertEqual(result.total_count, 1)
        self.assertFalse(NotificationRecord.objects.filter(pk=stuck_record.pk).exists())
        self.assertTrue(
            NotificationRecord.objects.filter(pk=recent_terminal.pk).exists()
        )


class PruneNotificationRecordsCommandTestCase(TestCase):
    """Smoke tests for prune_notification_records management command."""

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
        NotificationProcessingConfig.objects.all().delete()

    def test_command_with_no_config(self):
        """Test command outputs warning when no retention is configured."""
        out = StringIO()
        call_command("prune_notification_records", stdout=out)

        output = out.getvalue()
        self.assertIn("No retention_days configured", output)
        self.assertIn("kept indefinitely", output)

    def test_command_with_override_days(self):
        """Test command with --days override."""
        now = timezone.now()
        old_date = now - timedelta(days=31)

        NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SUCCESS,
            last_processed_at=old_date,
        )

        out = StringIO()
        call_command("prune_notification_records", days=30, stdout=out)

        output = out.getvalue()
        self.assertIn("Using override: 30 days retention", output)
        self.assertIn("Successfully deleted", output)
        self.assertIn("1 notification records", output)

    def test_command_with_dry_run(self):
        """Test command with --dry-run flag."""
        config = NotificationProcessingConfig.get_solo()
        config.retention_days = 30
        config.save()

        now = timezone.now()
        old_date = now - timedelta(days=31)

        record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SUCCESS,
            last_processed_at=old_date,
        )

        out = StringIO()
        call_command("prune_notification_records", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("[DRY RUN]", output)
        self.assertIn("Would delete", output)
        self.assertIn("1 notification records", output)
        self.assertTrue(NotificationRecord.objects.filter(pk=record.pk).exists())

    def test_command_with_config(self):
        """Test command uses configured retention days."""
        config = NotificationProcessingConfig.get_solo()
        config.retention_days = 45
        config.save()

        out = StringIO()
        call_command("prune_notification_records", stdout=out)

        output = out.getvalue()
        self.assertIn("Using configured retention: 45 days retention", output)
        self.assertIn("No records found to prune.", output)

    def test_command_shows_breakdown(self):
        """Test command shows status breakdown."""
        config = NotificationProcessingConfig.get_solo()
        config.retention_days = 30
        config.save()

        now = timezone.now()
        old_date = now - timedelta(days=31)

        NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.SUCCESS,
            last_processed_at=old_date,
        )
        NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.FAILED,
            last_processed_at=old_date,
        )

        out = StringIO()
        call_command("prune_notification_records", stdout=out)

        output = out.getvalue()
        self.assertIn("- success:", output)
        self.assertIn("- failed:", output)
        self.assertIn("Successfully deleted 2 notification records", output)

    def test_command_with_processing_days_override(self):
        """Test command with --processing-days override prunes stuck PROCESSING records."""
        now = timezone.now()

        stuck_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PROCESSING,
            process_started_at=now - timedelta(days=8),
        )

        out = StringIO()
        call_command(
            "prune_notification_records", days=30, processing_days=7, stdout=out
        )

        output = out.getvalue()
        self.assertIn("Using override: 7 days for stuck processing", output)
        self.assertIn("Successfully deleted", output)
        self.assertFalse(NotificationRecord.objects.filter(pk=stuck_record.pk).exists())

    def test_command_with_stuck_processing_config(self):
        """Test command uses configured stuck_processing_retention_days."""
        config = NotificationProcessingConfig.get_solo()
        config.retention_days = 30
        config.stuck_processing_retention_days = 7
        config.save()

        now = timezone.now()

        stuck_record = NotificationRecord.objects.create(
            subscription=self.subscription,
            payload={"test": "data"},
            status=ProcessingStatus.PROCESSING,
            process_started_at=now - timedelta(days=8),
        )

        out = StringIO()
        call_command("prune_notification_records", stdout=out)

        output = out.getvalue()
        self.assertIn("Using configured retention: 7 days for stuck processing", output)
        self.assertIn("stuck processing before", output)
        self.assertFalse(NotificationRecord.objects.filter(pk=stuck_record.pk).exists())
