from unittest import skip

from django.contrib.gis.geos import Point

from open_inwoner.utils.tests.test_migrations import TestMigrations

from ..models.product import ProductLocation


@skip("outdated")
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


@skip("outdated")
class TruncateProductSummaryMigrationTests(TestMigrations):
    app = "pdc"
    migrate_from = "0048_alter_product_summary"
    migrate_to = "0050_alter_product_summary"

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


@skip("outdated")
class NotTruncateProductSummaryMigrationTests(TestMigrations):
    app = "pdc"
    migrate_from = "0048_alter_product_summary"
    migrate_to = "0050_alter_product_summary"

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


@skip("outdated")
class CategoryProductThroughModelMigrationTests(TestMigrations):
    app = "pdc"
    migrate_from = "0050_alter_product_summary"
    migrate_to = "0052_auto_20230221_1518"

    def setUpBeforeMigration(self, apps):
        Category = apps.get_model("pdc", "Category")
        Product = apps.get_model("pdc", "Product")

        self.category_initial = Category.objects.create(
            name="Category Initial",
            slug="category_initial",
            path="initial",
            depth=1,
        )
        self.category_extra = Category.objects.create(
            name="Category Extra",
            slug="category_extra",
            path="extra",
            depth=1,
        )
        self.product = Product.objects.create(
            name="Product",
            slug="product",
        )
        self.product.categories.add(self.category_initial)

    def test_products_still_have_category(self):
        Product = self.apps.get_model("pdc", "Product")
        Category = self.apps.get_model("pdc", "Category")

        category_initial = Category.objects.get(id=self.category_initial.id)
        category_extra = Category.objects.get(id=self.category_extra.id)

        product = Product.objects.get(id=self.product.id)
        product.categories.add(category_extra, through_defaults={"order": 1})

        self.assertEqual(
            list(product.categories.all()),
            [category_initial, category_extra],
        )
