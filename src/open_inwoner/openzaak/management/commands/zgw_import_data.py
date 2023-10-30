import logging

from django.core.management.base import BaseCommand

from open_inwoner.openzaak.zgw_imports import (
    import_catalog_configs,
    import_zaaktype_configs,
    import_zaaktype_informatieobjecttype_configs,
    import_zaaktype_resultaattype_configs,
    import_zaaktype_statustype_configs,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import ZGW catalog data"

    def log_supplement_imports_to_stdout(
        self, import_func: callable, config_type: str
    ) -> None:
        """
        Convenience function for logging zaaktype config types to stdout

        Example input:
            import_func=import_zaaktype_informatieobjecttype_configs
            config_type="informatiebjecttype"

        Example output:
            imported 3 new zaaktype-informatiebjecttype configs
            AAA - zaaktype-aaa
              info-aaa-1
              info-aaa-2
            BBB - zaaktype-bbb
              info-bbb
        """
        imported = import_func()

        count = sum(len(t[1]) for t in imported)
        self.stdout.write(f"imported {count} new zaaktype-{config_type} configs")

        for ztc, config_types in sorted(imported, key=lambda t: str(t[0])):
            self.stdout.write(str(ztc))
            for c in sorted(map(str, config_types)):
                self.stdout.write(f"  {c}")

        self.stdout.write("")

    def handle(self, *args, **options):
        # catalogus config
        imported = import_catalog_configs()

        self.stdout.write(f"imported {len(imported)} new catalogus configs")
        for c in sorted(map(str, imported)):
            self.stdout.write(c)

        self.stdout.write("")

        # zaaktype config
        imported = import_zaaktype_configs()

        self.stdout.write(f"imported {len(imported)} new zaaktype configs")
        for c in sorted(map(str, imported)):
            self.stdout.write(c)

        self.stdout.write("")

        # supplemental configs
        self.log_supplement_imports_to_stdout(
            import_zaaktype_informatieobjecttype_configs, "informatiebjecttype"
        )
        self.log_supplement_imports_to_stdout(
            import_zaaktype_statustype_configs, "statustype"
        )
        self.log_supplement_imports_to_stdout(
            import_zaaktype_resultaattype_configs, "resultaattype"
        )
