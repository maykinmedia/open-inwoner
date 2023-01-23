import logging

from django.core.management.base import BaseCommand

from open_inwoner.openzaak.config import import_catalog_configs
from open_inwoner.openzaak.models import CatalogusConfig

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import ZGW catalog data"

    def handle(self, *args, **options):
        have = list(CatalogusConfig.objects.all())
        if have:
            self.stdout.write(f"have {len(have)} existing catalogi")
            for c in have:
                self.stdout.write(str(c))
            self.stdout.write("")

        imported = import_catalog_configs()

        self.stdout.write(f"imported {len(imported)} new catalogi")
        for c in sorted(imported):
            self.stdout.write(str(c))
