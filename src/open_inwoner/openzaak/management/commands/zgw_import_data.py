import logging

from django.core.management.base import BaseCommand

from open_inwoner.openzaak.config import import_catalog_configs, import_zaaktype_configs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import ZGW catalog data"

    def handle(self, *args, **options):
        imported = import_catalog_configs()

        self.stdout.write(f"imported {len(imported)} new catalogi")
        for c in sorted(map(str, imported)):
            self.stdout.write(c)
        self.stdout.write("")

        imported = import_zaaktype_configs()

        self.stdout.write(f"imported {len(imported)} new zaak_types")
        for c in sorted(map(str, imported)):
            self.stdout.write(c)
