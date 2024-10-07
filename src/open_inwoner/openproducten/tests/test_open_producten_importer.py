from unittest.mock import MagicMock
from uuid import uuid4

from django.test import TestCase

from open_inwoner.openproducten.producttypes_imports import (
    OpenProductenImporterMixin,
    _get_instance,
)
from open_inwoner.pdc.models import Tag
from open_inwoner.pdc.tests.factories import TagFactory

from .helpers import create_file_object


class TestOpenProductenImporter(TestCase):
    def setUp(self):
        self.client = MagicMock()

    def test_get_instance_should_return_instance_with_uuid(self):
        uuid = uuid4()
        tag = TagFactory.create(open_producten_uuid=uuid)

        self.assertEqual(_get_instance(Tag, uuid), tag)

    def test_get_instance_should_return_None_if_uuid_does_not_exist(self):
        uuid = uuid4()
        self.assertEqual(_get_instance(Tag, uuid), None)

    def test_add_to_log_list_should_append_created_objects_when_created(self):
        importer = OpenProductenImporterMixin(self.client)

        importer._add_to_log_list("a", True)

        self.assertEqual(importer.created_objects, ["a"])
        self.assertEqual(importer.updated_objects, [])

    def test_add_to_log_list_should_append_updated_objects_when_not_created(self):
        importer = OpenProductenImporterMixin(self.client)

        importer._add_to_log_list("a", False)

        self.assertEqual(importer.updated_objects, ["a"])
        self.assertEqual(importer.created_objects, [])

    def test_get_file_returns_none_when_client_returns_none(self):
        self.client.fetch_file.return_value = None
        importer = OpenProductenImporterMixin(self.client)
        file = importer._get_file("test")

        self.assertIsNone(file)

    def test_get_file_returns_file_instance_when_client_returns_file(self):
        self.client.fetch_file.return_value = create_file_object(b"content")
        importer = OpenProductenImporterMixin(self.client)
        file = importer._get_file("test/media/file.txt")

        self.assertEqual(file.original_filename, "file.txt")

    def test_get_image_returns_none_when_client_returns_none(self):
        self.client.fetch_file.return_value = None
        importer = OpenProductenImporterMixin(self.client)
        file = importer._get_image("test")

        self.assertIsNone(file)

    def test_get_image_returns_file_instance_when_client_returns_file(self):
        self.client.fetch_file.return_value = create_file_object(b"content")
        importer = OpenProductenImporterMixin(self.client)
        file = importer._get_image("test/media/file.png")

        self.assertEqual(file.original_filename, "file.png")
