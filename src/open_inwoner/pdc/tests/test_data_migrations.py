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


class TruncateProductSummaryMigrationTests(TestMigrations):
    app = "pdc"
    migrate_from = "0044_question_category_or_product_null"
    migrate_to = "0046_alter_product_summary"

    def setUpBeforeMigration(self, apps):
        self.ProductModel = apps.get_model("pdc", "Product")
        self.product = self.ProductModel.objects.create(
            name="product name",
            summary="t" * 350,
            content="some content",
            published=True,
        )

    def test_product_is_truncated_when_above_max_length(self):

        self.assertEqual(len(self.product.summary), 350)

        self.product.refresh_from_db()

        self.assertEqual(len(self.product.summary), 300)


class NotTruncateProductSummaryMigrationTests(TestMigrations):
    app = "pdc"
    migrate_from = "0044_question_category_or_product_null"
    migrate_to = "0046_alter_product_summary"

    def setUpBeforeMigration(self, apps):
        self.ProductModel = apps.get_model("pdc", "Product")
        self.product = self.ProductModel.objects.create(
            name="product name",
            summary="t" * 300,
            content="some content",
            published=True,
        )

    def test_product_is_not_truncated_when_below_max_length(self):

        self.assertEqual(len(self.product.summary), 300)

        self.product.refresh_from_db()

        self.assertEqual(len(self.product.summary), 300)
