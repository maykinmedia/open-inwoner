from django.core.management.base import BaseCommand

from notifications.models import NotificationProcessingConfig, NotificationRecord


class Command(BaseCommand):
    help = (
        "Delete old notification records based on retention settings configured in "
        "NotificationProcessingConfig. Deletes terminal-state records (SUCCESS, FAILED, "
        "SKIPPED) older than retention_hours, and optionally PROCESSING records whose "
        "worker was killed, older than stuck_processing_retention_hours."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--hours",
            type=int,
            help="Override terminal-state retention hours from config (for testing)",
        )
        parser.add_argument(
            "--processing-hours",
            type=int,
            help="Override stuck processing retention hours from config (for testing)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        config = NotificationProcessingConfig.get_solo()

        override_hours = options.get("hours")
        if override_hours is not None:
            retention_hours = override_hours
            self.stdout.write(f"Using override: {retention_hours} hours retention")
        elif config.retention_hours is not None:
            retention_hours = config.retention_hours
            self.stdout.write(
                f"Using configured retention: {retention_hours} hours retention"
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No retention_hours configured. Records will be kept indefinitely. "
                    "Set retention_hours in NotificationProcessingConfig or use --hours flag."
                )
            )
            return

        override_processing_hours = options.get("processing_hours")
        if override_processing_hours is not None:
            stuck_processing_retention_hours = override_processing_hours
            self.stdout.write(
                f"Using override: {stuck_processing_retention_hours} hours for stuck processing"
            )
        elif config.stuck_processing_retention_hours is not None:
            stuck_processing_retention_hours = config.stuck_processing_retention_hours
            self.stdout.write(
                f"Using configured retention: {stuck_processing_retention_hours} hours for stuck processing"
            )
        else:
            stuck_processing_retention_hours = None

        result = NotificationRecord.objects.prune_old_records(
            retention_hours=retention_hours,
            stuck_processing_retention_hours=stuck_processing_retention_hours,
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
                    f"(terminal states before {result.cutoff_date.isoformat()}"
                    + (
                        f", stuck processing before {result.stuck_processing_cutoff_date.isoformat()}"
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
                    f"(terminal states before {result.cutoff_date.isoformat()}"
                    + (
                        f", stuck processing before {result.stuck_processing_cutoff_date.isoformat()}"
                        if result.stuck_processing_cutoff_date
                        else ""
                    )
                    + ")"
                )
            )
