from django.core.management.base import BaseCommand

from notifications.models import NotificationProcessingConfig, NotificationRecord


class Command(BaseCommand):
    help = (
        "Delete old notification records based on retention settings configured in "
        "NotificationProcessingConfig. Deletes terminal-state records (SUCCESS, FAILED, "
        "SKIPPED) older than retention_days, and optionally PROCESSING records whose "
        "worker was killed, older than stuck_processing_retention_days."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--days",
            type=int,
            help="Override terminal-state retention days from config (for testing)",
        )
        parser.add_argument(
            "--processing-days",
            type=int,
            help="Override stuck processing retention days from config (for testing)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        config = NotificationProcessingConfig.get_solo()

        override_days = options.get("days")
        if override_days is not None:
            retention_days = override_days
            self.stdout.write(f"Using override: {retention_days} days retention")
        elif config.retention_days is not None:
            retention_days = config.retention_days
            self.stdout.write(
                f"Using configured retention: {retention_days} days retention"
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No retention_days configured. Records will be kept indefinitely. "
                    "Set retention_days in NotificationProcessingConfig or use --days flag."
                )
            )
            return

        override_processing_days = options.get("processing_days")
        if override_processing_days is not None:
            stuck_processing_retention_days = override_processing_days
            self.stdout.write(
                f"Using override: {stuck_processing_retention_days} days for stuck processing"
            )
        elif config.stuck_processing_retention_days is not None:
            stuck_processing_retention_days = config.stuck_processing_retention_days
            self.stdout.write(
                f"Using configured retention: {stuck_processing_retention_days} days for stuck processing"
            )
        else:
            stuck_processing_retention_days = None

        result = NotificationRecord.objects.prune_old_records(
            retention_days=retention_days,
            stuck_processing_retention_days=stuck_processing_retention_days,
            dry_run=dry_run,
        )

        if not result.has_records:
            self.stdout.write(self.style.SUCCESS("No records found to prune."))
            return

        for status_name, count in result.breakdown_by_status.items():
            self.stdout.write(f"  - {status_name}: {count} records")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {result.total_count} notification records "
                    f"(terminal states before {result.cutoff_date.date()}"
                    + (
                        f", stuck processing before {result.stuck_processing_cutoff_date.date()}"
                        if result.stuck_processing_cutoff_date
                        else ""
                    )
                    + ")"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {result.total_count} notification records "
                    f"(terminal states before {result.cutoff_date.date()}"
                    + (
                        f", stuck processing before {result.stuck_processing_cutoff_date.date()}"
                        if result.stuck_processing_cutoff_date
                        else ""
                    )
                    + ")"
                )
            )
