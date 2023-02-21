from django.contrib.gis.geos import Point

from open_inwoner.utils.tests.test_migrations import TestMigrations

from ..models.product import ProductLocation


class ProductLocationUUIDMigrationTests(TestMigrations):
    app = "pdc"
    migrate_from = "0045_auto_20230221_0954"
    migrate_to = "0046_auto_20230221_0954"

    def setUpBeforeMigration(self, apps):
        self.ProductLocationModel = apps.get_model("pdc", "ProductLocation")
        self.product_location = ProductLocation.objects.create(
            name="a location",
            street="street_name",
            postcode="1022xm",
            geometry=Point(5, 52),
        )

    def test_uuid_is_set(self):
        self.assertIsNotNone(self.product_location.uuid)
