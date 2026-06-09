from django.core.management.base import BaseCommand, CommandError

from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.zgw_imports import (
    ExclusionReason,
    ZGWCatalogusImporter,
)


class Command(BaseCommand):
    help = "Import ZGW catalog data"

    def handle(self, *args, **options):
        if not ZGWApiGroupConfig.objects.exists():
            self.stdout.write(
                "Please define at least one ZGWApiGroupConfig before running this command."
            )
            return

        importers = [
            ZGWCatalogusImporter(api_group)
            for api_group in ZGWApiGroupConfig.objects.all()
        ]

        results = []
        for importer in importers:
            result = importer.import_all()
            results.append(result)

        self.stdout.write("\n".join(result.pretty_print() for result in results))

        has_errors = any(
            excluded.reason
            in (ExclusionReason.API_ERROR, ExclusionReason.DATABASE_ERROR)
            for result in results
            for excluded in result.all_excluded()
        )
        if has_errors:
            raise CommandError("Import completed with errors")
