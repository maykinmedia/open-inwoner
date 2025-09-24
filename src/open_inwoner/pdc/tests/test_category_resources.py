from collections import OrderedDict

from django.test import TestCase

import tablib
from import_export.exceptions import ImportExportError

from open_inwoner.pdc.models import Category
from open_inwoner.pdc.resources import CategoryExportResource, CategoryImportResource

from .factories import CategoryFactory


class TestCategoryImportResource(TestCase):
    def setUp(self):
        self.category = CategoryFactory.build()
        self.resource = CategoryImportResource()

    def test_import_saves_category(self):
        dataset = tablib.Dataset(
            [
                self.category.name,
                "<p>Test description</p>",
                "",
            ],
            headers=[
                "name",
                "description",
                "slug",
            ],
        )
        result = self.resource.import_data(dataset, raise_errors=True)
        qs = Category.objects.filter(name=self.category.name)

        self.assertEqual(qs.count(), 1)

    def test_import_raises_import_export_error_when_headers_are_missing(self):
        dataset = tablib.Dataset(
            [
                self.category.name,
            ],
            headers=[""],
        )
        expected_error_message_list = [
            "description",
            "name",
            "slug",
        ]
        with self.assertRaises(ImportExportError) as e:
            self.resource.import_data(dataset, raise_errors=True)

        error_message_list = sorted(
            e.exception.args[0].replace("\n", "").split()[-1].split(",")
        )

        self.assertEqual(error_message_list, expected_error_message_list)

    def test_import_creates_slug_field_when_it_is_not_given(self):
        dataset = tablib.Dataset(
            [
                self.category.name,
                "<p>Test description</p>",
                "",
            ],
            headers=[
                "name",
                "description",
                "slug",
            ],
        )
        self.resource.import_data(dataset)
        qs = Category.objects.filter(name=self.category.name)

        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].slug, self.category.slug)

    def test_import_updates_category_when_slug_field_is_given(self):
        category = CategoryFactory.create()
        updated_category = CategoryFactory.build()
        dataset = tablib.Dataset(
            [
                updated_category.name,
                "<p>Updated description</p>",
                category.slug,
            ],
            headers=[
                "name",
                "description",
                "slug",
            ],
        )
        result = self.resource.import_data(dataset)
        qs = Category.objects.filter(slug=category.slug)

        self.assertEqual(result.totals["update"], 1)
        self.assertEqual(qs[0].name, updated_category.name)

    def test_import_builds_right_path_for_initial_category(self):
        dataset = tablib.Dataset(
            [
                self.category.name,
                "<p>Test description</p>",
                "",
            ],
            headers=[
                "name",
                "description",
                "slug",
            ],
        )
        self.resource.import_data(dataset)
        qs = Category.objects.filter(name=self.category.name)

        self.assertEqual(qs[0].path, "0001")

    def test_import_builds_right_path_for_additional_category(self):
        CategoryFactory.create()
        category = CategoryFactory.build()
        dataset = tablib.Dataset(
            [
                category.name,
                "<p>Test description</p>",
                "",
            ],
            headers=[
                "name",
                "description",
                "slug",
            ],
        )
        self.resource.import_data(dataset)
        qs = Category.objects.filter(name=category.name)

        self.assertEqual(qs[0].path, "0002")


class TestCategoryExportResource(TestCase):
    def setUp(self):
        self.category = CategoryFactory()
        self.resource = CategoryExportResource()

    def test_export_returns_expected_row(self):
        dataset = self.resource.export()

        self.assertEqual(
            dataset.dict,
            [
                OrderedDict(
                    [
                        (dataset.headers[0], self.category.name),
                        (dataset.headers[1], self.category.slug),
                        (
                            dataset.headers[2],
                            self.category.description.html
                            if self.category.description
                            else "",
                        ),
                        (dataset.headers[3], self.category.path),
                    ]
                ),
            ],
        )
