from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from django.test import TestCase

import open_inwoner.pdc.models as pdc_models
from open_inwoner.openproducten.producttypes_imports import CategoryImporter
from open_inwoner.pdc.tests.factories import CategoryFactory, QuestionFactory

from .helpers import (
    create_category,
    create_complete_category,
    create_question,
    get_all_category_objects,
)


@patch(
    "open_inwoner.openproducten.producttypes_imports.OpenProductenImporterMixin._get_image",
    new=Mock(return_value=None),
)
class TestCategoryImporter(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        patch.stopall()
        super().tearDownClass()

    def setUp(self):
        self.client = MagicMock()

    def test_update_or_create_category(self):
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):
                uuid = uuid4()

                if not create:
                    CategoryFactory.create(open_producten_uuid=uuid)

                category = create_category(uuid)

                importer = CategoryImporter(self.client)
                instance = importer._update_or_create_category(category)

                self.assertEqual(pdc_models.Category.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.name, category.name)

                # Subtest does not reset db
                pdc_models.Category.objects.all().delete()

    def test_update_category_to_parent_root(self):
        category_uuid = uuid4()

        existing_parent = CategoryFactory.create(open_producten_uuid=uuid4())
        existing_category_instance = existing_parent.add_child(
            name="child", open_producten_uuid=category_uuid
        )

        parent_instance = None
        data = {
            "open_producten_uuid": category_uuid,
            "name": "category",
            "slug": "category",
            "published": False,
            "description": "desc",
            "icon": None,
            "image": None,
        }
        importer = CategoryImporter(self.client)
        updated_instance = importer._update_category(
            existing_category_instance, parent_instance, data
        )

        self.assertEqual(updated_instance.get_parent(update=True), None)

    def test_update_category_to_parent(self):
        category_uuid = uuid4()

        existing_category_instance = CategoryFactory.create(
            open_producten_uuid=category_uuid
        )

        new_parent_instance = CategoryFactory.create(open_producten_uuid=uuid4())

        data = {
            "open_producten_uuid": category_uuid,
            "name": "category",
            "slug": "category",
            "published": False,
            "description": "desc",
            "icon": None,
            "image": None,
        }
        importer = CategoryImporter(self.client)
        updated_instance = importer._update_category(
            existing_category_instance, new_parent_instance, data
        )

        self.assertEqual(updated_instance.get_parent(update=True), new_parent_instance)

    def test_create_category_on_root(self):
        category_uuid = uuid4()

        parent_instance = None
        data = {
            "open_producten_uuid": category_uuid,
            "name": "category",
            "slug": "category",
            "published": False,
            "description": "desc",
            "icon": None,
            "image": None,
        }
        importer = CategoryImporter(self.client)
        created_instance = importer._create_category(parent_instance, data)

        self.assertEqual(created_instance.get_parent(update=True), None)

    def test_create_category_on_parent(self):
        category_uuid = uuid4()

        parent_instance = CategoryFactory.create(open_producten_uuid=uuid4())
        data = {
            "open_producten_uuid": category_uuid,
            "name": "category",
            "slug": "category",
            "published": False,
            "description": "desc",
            "icon": None,
            "image": None,
        }
        importer = CategoryImporter(self.client)
        created_instance = importer._create_category(parent_instance, data)

        self.assertEqual(created_instance.get_parent(update=True), parent_instance)

    def test_update_or_create_question(self):
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):
                uuid = uuid4()

                category = CategoryFactory()

                if not create:
                    pdc_models.Question.objects.create(
                        open_producten_uuid=uuid,
                        question="?",
                        answer="b",
                        category=category,
                    )

                question = create_question(uuid)

                importer = CategoryImporter(self.client)
                importer._update_or_create_question(question, category=category)

                instance = pdc_models.Question.objects.first()

                self.assertEqual(pdc_models.Question.objects.count(), 1)
                self.assertEqual(instance.open_producten_uuid, uuid)
                self.assertEqual(instance.question, question.question)

                # Subtest does not reset db
                pdc_models.Question.objects.all().delete()

    @patch(
        "open_inwoner.openproducten.producttypes_imports.CategoryImporter._handle_category_parent"
    )
    def test_handle_category_category_is_handled_when_not_in_handled_categories(
        self, mock_handle_category_parent
    ):
        category_uuid = uuid4()
        category = create_category(category_uuid)
        importer = CategoryImporter(self.client)
        importer._handle_category(category)

        mock_handle_category_parent.assert_called_once()

    @patch(
        "open_inwoner.openproducten.producttypes_imports.CategoryImporter._handle_category_parent"
    )
    def test_handle_category_category_is_not_handled_when_in_handled_categories(
        self, mock_handle_category_parent
    ):
        category_uuid = uuid4()
        category = create_category(category_uuid)
        importer = CategoryImporter(self.client)
        importer.handled_categories = {category_uuid}
        importer._handle_category(category)

        mock_handle_category_parent.assert_not_called()

    @patch(
        "open_inwoner.openproducten.producttypes_imports.CategoryImporter._handle_category"
    )
    def test_handle_category_parent_is_handled_when_not_in_handled_categories(
        self, mock_handle_category
    ):
        category_uuid = uuid4()
        category = create_category(category_uuid)
        importer = CategoryImporter(self.client)
        importer.categories = [category]
        importer._handle_category_parent(category_uuid)

        mock_handle_category.assert_called_once_with(category)

    @patch(
        "open_inwoner.openproducten.producttypes_imports.CategoryImporter._handle_category"
    )
    def test_handle_category_parent_is_not_handled_when_in_handled_categories(
        self, mock_handle_category
    ):
        category_uuid = uuid4()
        importer = CategoryImporter(self.client)
        importer.handled_categories = {category_uuid}
        importer._handle_category_parent(category_uuid)

        mock_handle_category.assert_not_called()

    def test_updated_objects_are_not_deleted(self):
        category = CategoryFactory.create(open_producten_uuid=uuid4())
        QuestionFactory.create(open_producten_uuid=uuid4())

        importer = CategoryImporter(self.client)
        importer.handled_categories.add(category.open_producten_uuid)
        importer._delete_non_updated_objects()
        self.assertEqual(importer.deleted_count, 0)

    def test_non_updated_objects_are_deleted(self):
        category = CategoryFactory.create(open_producten_uuid=uuid4())
        QuestionFactory.create(open_producten_uuid=uuid4(), category=category)

        importer = CategoryImporter(self.client)

        importer._delete_non_updated_objects()
        self.assertEqual(importer.deleted_count, 2)

    def test_non_updated_objects_without_open_producten_uuid_are_kept(self):
        CategoryFactory.create()
        QuestionFactory.create()

        importer = CategoryImporter(self.client)

        importer._delete_non_updated_objects()
        self.assertEqual(importer.deleted_count, 0)

    def test_complete_import_with_new_objects(self):
        parent = create_category(uuid4())
        category = create_complete_category("test2")
        category.parent_category = parent.id

        self.client.fetch_categories_no_cache.return_value = [
            category,
            parent,
        ]
        importer = CategoryImporter(self.client)
        created, updated, deleted = importer.import_categories()

        self.assertEqual(pdc_models.Category.objects.count(), 2)
        self.assertEqual(pdc_models.Question.objects.count(), 1)

        all_objects = get_all_category_objects()

        self.assertEqual(updated, [])
        self.assertEqual(deleted, 0)
        self.assertEqual(
            sorted({obj.open_producten_uuid for obj in created}),
            sorted({obj.open_producten_uuid for obj in all_objects}),
        )

    def test_complete_import_with_existing_objects(self):
        parent = create_category(uuid4())
        category = create_complete_category("test2")
        category.parent_category = parent.id

        self.client.fetch_categories_no_cache.return_value = [
            category,
            parent,
        ]
        for _ in range(2):
            importer = CategoryImporter(self.client)
            created, updated, deleted = importer.import_categories()

            self.assertEqual(pdc_models.Category.objects.count(), 2)
            self.assertEqual(pdc_models.Question.objects.count(), 1)

        all_objects = get_all_category_objects()

        self.assertEqual(created, [])
        self.assertEqual(deleted, 0)
        self.assertEqual(
            sorted({obj.open_producten_uuid for obj in updated}),
            sorted({obj.open_producten_uuid for obj in all_objects}),
        )

    def test_complete_import_without_objects(self):
        parent = create_category(uuid4())
        category = create_complete_category("test2")
        category.parent_category = parent.id

        for return_value in (
            [
                category,
                parent,
            ],
            [],
        ):
            self.client.fetch_categories_no_cache.return_value = return_value
            importer = CategoryImporter(self.client)
            created, updated, deleted = importer.import_categories()

        self.assertEqual(created, [])
        self.assertEqual(updated, [])
        self.assertEqual(deleted, 3)
