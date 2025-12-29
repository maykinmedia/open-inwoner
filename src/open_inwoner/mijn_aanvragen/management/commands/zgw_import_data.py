from django.core.management.base import BaseCommand

from open_inwoner.mijn_aanvragen.models import ZGWApiGroupConfig
from open_inwoner.mijn_aanvragen.zgw_imports import (
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

        outputs: list[str] = []
        for importer in importers:
            result = importer.import_all()
            outputs.append(result.pretty_print())

        self.stdout.write("\n".join(outputs))
