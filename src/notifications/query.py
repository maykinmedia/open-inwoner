import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Union

from django.db import models, transaction
from django.db.models import Count, Q
from django.utils import timezone

from .constants import ProcessingStatus
from .exceptions import (
    NotificationAlreadyProcessedError,
    NotificationRecordLockError,
    NotificationSkippedException,
)

if TYPE_CHECKING:
    from .models import NotificationRecord


@dataclass
class PruneResult:
    """Result of a prune operation with detailed statistics."""

    retention_days: int
    cutoff_date: datetime
    stuck_processing_retention_days: int | None
    stuck_processing_cutoff_date: datetime | None
    total_count: int
    breakdown_by_status: dict[str, int]
    deleted: bool = False

    @property
    def has_records(self) -> bool:
        return self.total_count > 0


class NotificationsConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("notifications_api_service")


class NotificationRecordManager(models.Manager):
    def prune_old_records(
        self,
        retention_days: int,
        *,
        stuck_processing_retention_days: int | None = None,
        dry_run: bool = False,
    ) -> PruneResult:
        """
        Prune notification records older than the specified retention period.

        Deletes records in final states (SUCCESS, FAILED, SKIPPED). Optionally
        also deletes PROCESSING records whose worker was killed before completing.

        Args:
            retention_days: Number of days to retain terminal-state records
            stuck_processing_retention_days: Number of days after which PROCESSING
                records are considered stuck and pruned. None skips this cleanup.
            dry_run: If True, only calculate what would be deleted without deleting

        Returns:
            PruneResult with detailed statistics about the operation
        """
        now = timezone.now()
        cutoff_date = now - timedelta(days=retention_days)

        terminal_q = Q(
            last_processed_at__lt=cutoff_date,
            status__in=ProcessingStatus.final_statuses(),
        )

        stuck_processing_cutoff_date = None
        if stuck_processing_retention_days is not None:
            stuck_processing_cutoff_date = now - timedelta(
                days=stuck_processing_retention_days
            )
            combined_q = terminal_q | Q(
                process_started_at__lt=stuck_processing_cutoff_date,
                status=ProcessingStatus.PROCESSING,
            )
        else:
            combined_q = terminal_q

        base_query = self.filter(combined_q)

        # Calculate breakdown by status in a single query
        status_counts = base_query.values("status").annotate(count=Count("id"))
        breakdown = {item["status"]: item["count"] for item in status_counts}
        total_count = sum(breakdown.values()) if breakdown else 0

        # Actually delete if not dry run
        deleted = False
        if not dry_run and total_count > 0:
            with transaction.atomic():
                # Lock records for deletion to prevent concurrent modifications
                records_to_delete = base_query.select_for_update()
                count_deleted, _ = records_to_delete.delete()
                deleted = count_deleted > 0

        return PruneResult(
            retention_days=retention_days,
            cutoff_date=cutoff_date,
            stuck_processing_retention_days=stuck_processing_retention_days,
            stuck_processing_cutoff_date=stuck_processing_cutoff_date,
            total_count=total_count,
            breakdown_by_status=breakdown,
            deleted=deleted,
        )

    @contextmanager
    def lock_for_processing(self, record: Union[uuid.UUID, str, "NotificationRecord"]):
        """
        Context manager for acquiring an exclusive lock on a notification record.

        Uses an atomic database UPDATE operation to implement optimistic locking.
        The database guarantees that the WHERE clause evaluation and UPDATE happen
        atomically - no other transaction can see or modify the row in between.

        Args:
            record: Either a NotificationRecord instance or a primary key (UUID
                or its string representation)

        Usage:
            # Using a primary key
            with NotificationRecord.objects.lock_for_processing(record_pk) as record:
                # Process the notification
                process_notification(record)

            # Using an instance
            record = NotificationRecord.objects.get(pk=record_pk)
            with NotificationRecord.objects.lock_for_processing(record) as record:
                # Process the notification
                process_notification(record)

        Raises:
            NotificationAlreadyProcessedError: If the record is already in a final state
            NotificationRecordLockError: If the record is already locked (concurrent access)
            NotificationRecord.DoesNotExist: If the record doesn't exist
        """
        # Get the record if a pk was provided, otherwise use the instance
        match record:
            case uuid.UUID() | str():
                record_pk = record
                record = self.get(pk=record_pk)
            case _:
                record_pk = record.pk

        # Atomic test-and-set: try to acquire the lock by transitioning to PROCESSING
        # The PROCESSING status acts as both a lock and a state indicator
        rows_updated = self.filter(
            pk=record_pk, status=ProcessingStatus.PENDING
        ).update(
            status=ProcessingStatus.PROCESSING,
            process_started_at=timezone.now(),
        )

        if rows_updated == 0:
            record.refresh_from_db()
            if record.status in ProcessingStatus.final_statuses():
                raise NotificationAlreadyProcessedError(
                    f"Notification record {record_pk} already processed with status: {record.status}"
                )
            raise NotificationRecordLockError(
                f"Notification record {record_pk} already locked or not pending"
            )

        exception_occurred = False
        skipped = False
        error_message = ""
        try:
            # Refresh to get latest data after acquiring lock
            record.refresh_from_db()
            yield record
        except NotificationSkippedException as e:
            # Special case: mark as skipped instead of failed
            skipped = True
            error_message = str(e)
            raise
        except Exception as e:
            exception_occurred = True
            error_message = str(e)
            raise
        finally:
            # Update final status based on whether exception occurred
            if skipped:
                self.filter(pk=record_pk).update(
                    status=ProcessingStatus.SKIPPED,
                    last_processed_at=timezone.now(),
                    processing_error=error_message,
                )
            elif exception_occurred:
                self.filter(pk=record_pk).update(
                    status=ProcessingStatus.FAILED,
                    last_processed_at=timezone.now(),
                    processing_error=error_message,
                )
            else:
                self.filter(pk=record_pk).update(
                    status=ProcessingStatus.SUCCESS,
                    last_processed_at=timezone.now(),
                )
