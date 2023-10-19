import logging

from django.core.management.base import BaseCommand

from open_inwoner.openzaak.zgw_imports import (
    import_catalog_configs,
    import_zaaktype_configs,
    import_zaaktype_informatieobjecttype_configs,
    import_zaaktype_statustype_configs,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import ZGW catalog data"

    def handle(self, *args, **options):
        imported = import_catalog_configs()

        self.stdout.write(f"imported {len(imported)} new catalogus configs")
        for c in sorted(map(str, imported)):
            self.stdout.write(c)

        self.stdout.write("")

        imported = import_zaaktype_configs()

        self.stdout.write(f"imported {len(imported)} new zaaktype configs")
        for c in sorted(map(str, imported)):
            self.stdout.write(c)

        self.stdout.write("")

        imported = import_zaaktype_informatieobjecttype_configs()

        count = sum(len(t[1]) for t in imported)

        self.stdout.write(f"imported {count} new zaaktype-informatiebjecttype configs")
        for ztc, info_types in sorted(imported, key=lambda t: str(t[0])):
            self.stdout.write(str(ztc))
            for c in sorted(map(str, info_types)):
                self.stdout.write(f"  {c}")

        self.stdout.write("")

        imported = import_zaaktype_statustype_configs()

        count = sum(len(t[1]) for t in imported)

        self.stdout.write(f"imported {count} new zaaktype-statustype configs")
        for ztc, status_types in sorted(imported, key=lambda t: str(t[0])):
            self.stdout.write(str(ztc))
            for c in sorted(map(str, status_types)):
                self.stdout.write(f"  {c}")
