from django.core.management import BaseCommand, CommandError

from open_inwoner.utils.virus_scan import (
    ScanStatus,
    VirusScanNotConfigured,
    scan_filer_files,
)


class Command(BaseCommand):
    help = (
        "Scans all filer files (including images) for viruses using the ClamAV configuration from "
        "the site configuration. Exits with code 2 if virus scanning is not "
        "configured, and with code 1 if any file is infected or could not be "
        "scanned."
    )

    def handle(self, *args, **options):
        try:
            results = scan_filer_files()
        except VirusScanNotConfigured as exc:
            raise CommandError(str(exc), returncode=2) from exc

        count = 0
        failed = []
        for item in results:
            count += 1
            if item.result.status != ScanStatus.clean:
                failed.append(item)

        if not failed:
            self.stdout.write(
                self.style.SUCCESS(f"Scanned {count} items and no viruses found")
            )
            return

        for item in failed:
            filer_file = item.file
            status = item.result.status
            style = (
                self.style.ERROR
                if status == ScanStatus.infected
                else self.style.WARNING
            )
            self.stdout.write(
                style(
                    f"ID: {filer_file.pk}\n"
                    f"  Filename: {filer_file.original_filename}\n"
                    f"  URL: {filer_file.url}\n"
                    f"  Result: {status} {item.result.detail}".rstrip()
                )
            )

        infected = sum(
            1 for item in failed if item.result.status == ScanStatus.infected
        )
        raise CommandError(
            f"Scanned {count} items: {infected} infected, "
            f"{len(failed) - infected} could not be scanned",
            returncode=1,
        )
