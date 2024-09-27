from django.core.management.base import BaseCommand

from open_inwoner.openproducten.clients import build_open_producten_client
from open_inwoner.openproducten.models import OpenProductenConfig
from open_inwoner.openproducten.producttypes_imports import (
    CategoryImporter,
    ProductTypeImporter,
)


class Command(BaseCommand):
    help = "Import product types"

    def handle(self, *args, **options):
        if OpenProductenConfig.objects.count() == 0:
            self.stdout.write(
                "Please define the OpenProductenConfig before running this command."
            )
            return
        client = build_open_producten_client()
        category_importer = CategoryImporter(client)
        product_type_importer = ProductTypeImporter(client)

        (
            created_category_objects,
            updated_category_objects,
            deleted_category_count,
        ) = category_importer.import_categories()
        (
            created_product_type_objects,
            updated_product_type_objects,
            deleted_product_type_count,
        ) = product_type_importer.import_producttypes()

        updated = updated_category_objects + updated_product_type_objects
        created = created_category_objects + created_product_type_objects
        deleted = deleted_category_count + deleted_product_type_count

        self.stdout.write(f"deleted {deleted} object(s):\n")
        self.stdout.write(f"updated {len(updated)} exising object(s)")
        self.stdout.write(f"created {len(created)} new object(s):\n")

        for instance in created:
            self.stdout.write(
                f"{type(instance).__name__}: {instance.open_producten_uuid}"
            )
