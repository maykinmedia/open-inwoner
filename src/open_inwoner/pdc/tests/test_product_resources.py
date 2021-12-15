from collections import OrderedDict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

import tablib
from freezegun import freeze_time
from import_export.exceptions import ImportExportError

from ..models import Product
from ..resources import ProductExportResource, ProductImportResource
from .factories import CategoryFactory, ProductFactory


class TestProductImportResource(TestCase):
    def setUp(self):
        self.category = CategoryFactory()
        self.product = ProductFactory.build(categories=(self.category,))
        self.resource = ProductImportResource()

    def test_import_saves_product_with_existing_categories(self):
        dataset = tablib.Dataset(
            [
                self.product.name,
                self.product.summary,
                self.product.content,
                self.category.slug,
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            headers=[
                "name",
                "summary",
                "content",
                "categories",
                "slug",
                "link",
                "related_products",
                "tags",
                "costs",
                "organizations",
            ],
        )
        self.resource.import_data(dataset)
        qs = Product.objects.filter(name=self.product.name)

        self.assertEqual(qs.count(), 1)

    def test_import_raises_import_export_error_when_headers_are_missing(self):
        dataset = tablib.Dataset(
            [
                self.product.name,
            ],
            headers=[""],
        )
        expected_error_message_list = [
            "categories",
            "content",
            "costs",
            "link",
            "name",
            "organizations",
            "related_products",
            "slug",
            "summary",
            "tags",
        ]
        with self.assertRaises(ImportExportError) as e:
            self.resource.import_data(dataset, raise_errors=True)

        error_message_list = sorted(
            e.exception.args[0].replace("\n", "").split()[-1].split(",")
        )
        self.assertEqual(error_message_list, expected_error_message_list)

    def test_import_raises_validation_error_when_category_value_is_null(self):
        dataset = tablib.Dataset(
            [
                self.product.name,
                self.product.summary,
                self.product.content,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            headers=[
                "name",
                "summary",
                "content",
                "categories",
                "slug",
                "link",
                "related_products",
                "tags",
                "costs",
                "organizations",
            ],
        )
        with self.assertRaises(ValidationError) as e:
            self.resource.import_data(dataset, raise_errors=True)

        self.assertEqual(
            e.exception.message,
            "The field categories is required",
        )

    def test_import_raises_validation_error_when_category_does_not_exist(self):
        dataset = tablib.Dataset(
            [
                self.product.name,
                self.product.summary,
                self.product.content,
                "wrong-category",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            headers=[
                "name",
                "summary",
                "content",
                "categories",
                "slug",
                "link",
                "related_products",
                "tags",
                "costs",
                "organizations",
            ],
        )
        with self.assertRaises(ValidationError) as e:
            self.resource.import_data(dataset, raise_errors=True)

        self.assertEqual(e.exception.message, "The category you entered does not exist")

    def test_import_creates_slug_field_when_it_is_not_given(self):
        dataset = tablib.Dataset(
            [
                self.product.name,
                self.product.summary,
                self.product.content,
                self.category.slug,
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            headers=[
                "name",
                "summary",
                "content",
                "categories",
                "slug",
                "link",
                "related_products",
                "tags",
                "costs",
                "organizations",
            ],
        )
        self.resource.import_data(dataset)
        qs = Product.objects.filter(name=self.product.name)

        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].slug, self.product.slug)

    def test_import_updates_product_when_slug_field_is_given(self):
        self.product.save()
        updated_product = ProductFactory.build(categories=(self.category,))
        dataset = tablib.Dataset(
            [
                updated_product.name,
                updated_product.summary,
                updated_product.content,
                self.category.slug,
                self.product.slug,
                "",
                "",
                "",
                "",
                "",
            ],
            headers=[
                "name",
                "summary",
                "content",
                "categories",
                "slug",
                "link",
                "related_products",
                "tags",
                "costs",
                "organizations",
            ],
        )
        result = self.resource.import_data(dataset)
        qs = Product.objects.filter(name=updated_product.name)

        self.assertEqual(result.totals["update"], 1)
        self.assertEqual(qs[0].name, updated_product.name)
        self.assertEqual(qs[0].summary, updated_product.summary)
        self.assertEqual(qs[0].content, updated_product.content)


class TestProductExportResource(TestCase):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.category = CategoryFactory()
        self.product = ProductFactory(categories=(self.category,))
        self.resource = ProductExportResource()

    def test_export_returns_expected_row(self):
        self.maxDiff = None
        dataset = self.resource.export()
        category_slug = self.product.categories.all()[0].slug

        self.assertEqual(
            dataset.dict,
            [
                OrderedDict(
                    [
                        (dataset.headers[0], self.product.name),
                        (dataset.headers[1], self.product.slug),
                        (dataset.headers[2], self.product.summary),
                        (dataset.headers[3], ""),
                        (dataset.headers[4], self.product.content),
                        (dataset.headers[5], category_slug),
                        (dataset.headers[6], ""),
                        (dataset.headers[7], ""),
                        (dataset.headers[8], ""),
                        (dataset.headers[9], Decimal("0.00")),
                        (dataset.headers[10], "2021-10-18 15:00:00"),
                        (dataset.headers[11], "2021-10-18 15:00:00"),
                    ]
                ),
            ],
        )
