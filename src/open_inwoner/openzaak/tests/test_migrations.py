from django.db import connection
from django.test import tag

from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


def _make_zaaktype_status_config(
    apps, description_tmp=None, doc_upload_description_tmp=None
):
    """Helper to create related objects and a ZaakTypeStatusTypeConfig at a historical state."""
    import uuid

    Service = apps.get_model("zgw_consumers", "Service")
    CatalogusConfig = apps.get_model("openzaak", "CatalogusConfig")
    ZaakTypeConfig = apps.get_model("openzaak", "ZaakTypeConfig")
    ZaakTypeStatusTypeConfig = apps.get_model("openzaak", "ZaakTypeStatusTypeConfig")

    service_obj = ServiceFactory(api_type="ztc")
    service = Service.objects.get(id=service_obj.id)

    uid = uuid.uuid4()
    catalogus = CatalogusConfig.objects.create(
        url=f"https://example.com/catalogussen/{uid}",
        domein="TEST",
        rsin="123456789",
        service=service,
    )
    zaaktype_config = ZaakTypeConfig.objects.create(
        urls=[f"https://example.com/zaaktypen/{uid}"],
        catalogus=catalogus,
        identificatie="TEST",
        omschrijving="Test ZaakType",
    )
    kwargs = dict(
        zaaktype_config=zaaktype_config,
        omschrijving="Test status",
        statustekst="Test",
        statustype_url=f"https://example.com/statustypen/{uid}",
        zaaktype_uuids=["a1591906-3368-470a-a957-4b8634c275a1"],
    )
    if description_tmp is not None:
        kwargs["description_tmp"] = description_tmp
    if doc_upload_description_tmp is not None:
        kwargs["document_upload_description_tmp"] = doc_upload_description_tmp
    return ZaakTypeStatusTypeConfig.objects.create(**kwargs)


@tag("migrations")
class DescriptionDataMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0071: description_tmp (markdown text) → description (ProseMirror).

    Scenarios:
    - Markdown content → converted to ProseMirror doc
    - Empty string → description stays NULL
    - Whitespace-only → description stays NULL
    """

    migrate_from = "0070_zaaktypestatustypeconfig_description_schema_1"
    migrate_to = "0071_zaaktypestatustypeconfig_description_data"
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        self.config_with_content = _make_zaaktype_status_config(
            apps, description_tmp="**Bold** answer"
        )
        self.config_empty = _make_zaaktype_status_config(apps, description_tmp="")
        self.config_whitespace = _make_zaaktype_status_config(
            apps, description_tmp="   "
        )

    def _get(self, config):
        ZaakTypeStatusTypeConfig = self.apps.get_model(
            "openzaak", "ZaakTypeStatusTypeConfig"
        )
        return ZaakTypeStatusTypeConfig.objects.get(id=config.id)

    def test_markdown_content_is_converted(self):
        config = self._get(self.config_with_content)
        self.assertIsNotNone(config.description.raw_data)
        self.assertEqual(config.description.raw_data["type"], "doc")

    def test_empty_content_is_skipped(self):
        config = self._get(self.config_empty)
        self.assertIsNone(config.description.raw_data)

    def test_whitespace_content_is_skipped(self):
        config = self._get(self.config_whitespace)
        self.assertIsNone(config.description.raw_data)


@tag("migrations")
class DocUploadDescriptionDataMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0074: document_upload_description_tmp → document_upload_description.

    Scenarios:
    - Markdown content → converted to ProseMirror doc
    - Empty string → field stays NULL
    - Whitespace-only → field stays NULL
    """

    migrate_from = "0073_zaaktypestatustypeconfig_doc_upload_description_schema_1"
    migrate_to = "0074_zaaktypestatustypeconfig_doc_upload_description_data"
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        self.config_with_content = _make_zaaktype_status_config(
            apps, doc_upload_description_tmp="**Upload** instructions"
        )
        self.config_empty = _make_zaaktype_status_config(
            apps, doc_upload_description_tmp=""
        )
        self.config_whitespace = _make_zaaktype_status_config(
            apps, doc_upload_description_tmp="   "
        )

    def _get(self, config):
        ZaakTypeStatusTypeConfig = self.apps.get_model(
            "openzaak", "ZaakTypeStatusTypeConfig"
        )
        return ZaakTypeStatusTypeConfig.objects.get(id=config.id)

    def test_markdown_content_is_converted(self):
        config = self._get(self.config_with_content)
        self.assertIsNotNone(config.document_upload_description.raw_data)
        self.assertEqual(config.document_upload_description.raw_data["type"], "doc")

    def test_empty_content_is_skipped(self):
        config = self._get(self.config_empty)
        self.assertIsNone(config.document_upload_description.raw_data)

    def test_whitespace_content_is_skipped(self):
        config = self._get(self.config_whitespace)
        self.assertIsNone(config.document_upload_description.raw_data)


@tag("migrations")
class FixEmptyStringProsemirrorFieldsTest(TestSuccessfulMigrations):
    migrate_from = "0077_catalogusconfig_found_in_api_and_more"
    migrate_to = "0078_fix_empty_string_prosemirror_fields"
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        # Use historical models to avoid field mismatch issues
        CatalogusConfig = apps.get_model("openzaak", "CatalogusConfig")
        ZaakTypeConfig = apps.get_model("openzaak", "ZaakTypeConfig")
        ZaakTypeStatusTypeConfig = apps.get_model(
            "openzaak", "ZaakTypeStatusTypeConfig"
        )
        Service = apps.get_model("zgw_consumers", "Service")

        # Create a service using factory, then get the historical instance
        service_factory = ServiceFactory(api_type="ztc")
        service = Service.objects.get(id=service_factory.id)

        # Create catalogus config with historical model
        catalogus = CatalogusConfig.objects.create(
            url="https://example.com/api/v1/catalogussen/test",
            domein="TEST",
            rsin="123456789",
            service=service,
        )

        # Create zaaktype config with historical model
        zaaktype_config = ZaakTypeConfig.objects.create(
            urls=["https://example.com/api/v1/zaaktypen/test"],
            catalogus=catalogus,
            identificatie="TEST-ZAAKTYPE",
            omschrijving="Test ZaakType",
        )

        # Create statustype configs with different scenarios
        # Scenario 1: Both fields have empty string "" (should be fixed to None)
        self.status_with_empty_strings = ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            omschrijving="Status with empty strings",
            statustekst="Test",
            statustype_url="https://example.com/statustypen/1",
            zaaktype_uuids=["a1591906-3368-470a-a957-4b8634c275a1"],
        )
        # Manually set empty strings in the database to simulate the import/export bug
        # The bug stores '""' (JSON-encoded empty string) not '' (empty string)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE openzaak_zaaktypestatustypeconfig SET description = %s, document_upload_description = %s WHERE id = %s",
                ('""', '""', self.status_with_empty_strings.id),
            )

        # Scenario 2: Fields have actual content (should be preserved)
        self.status_with_content = ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            omschrijving="Status with content",
            statustekst="Test",
            statustype_url="https://example.com/statustypen/2",
            zaaktype_uuids=["a1591906-3368-470a-a957-4b8634c275a1"],
        )
        # Use the .html property setter to properly convert HTML to ProseMirror format
        self.status_with_content.description.html = "<p>Status description</p>"
        self.status_with_content.document_upload_description.html = (
            "<p>Upload instructions</p>"
        )
        self.status_with_content.save()

        # Scenario 3: Fields are None (should remain None)
        self.status_with_none = ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            omschrijving="Status with None",
            statustekst="Test",
            statustype_url="https://example.com/statustypen/3",
            zaaktype_uuids=["a1591906-3368-470a-a957-4b8634c275a1"],
            description=None,
            document_upload_description=None,
        )

    def test_migration_fixes_empty_strings_and_preserves_valid_content(self):
        ZaakTypeStatusTypeConfig = self.apps.get_model(
            "openzaak", "ZaakTypeStatusTypeConfig"
        )

        # Scenario 1: Empty strings converted to None
        status_empty = ZaakTypeStatusTypeConfig.objects.get(
            id=self.status_with_empty_strings.id
        )
        self.assertIsNone(status_empty.description.raw_data)
        self.assertIsNone(status_empty.document_upload_description.raw_data)

        # Scenario 2: Content preserved as valid ProseMirror documents
        status_content = ZaakTypeStatusTypeConfig.objects.get(
            id=self.status_with_content.id
        )
        self.assertIsNotNone(status_content.description.raw_data)
        self.assertIsNotNone(status_content.document_upload_description.raw_data)
        self.assertIsInstance(status_content.description.raw_data, dict)
        self.assertEqual(status_content.description.raw_data.get("type"), "doc")
        self.assertIsInstance(status_content.document_upload_description.raw_data, dict)
        self.assertEqual(
            status_content.document_upload_description.raw_data.get("type"), "doc"
        )

        # Scenario 3: None values remain None
        status_none = ZaakTypeStatusTypeConfig.objects.get(id=self.status_with_none.id)
        self.assertIsNone(status_none.description.raw_data)
        self.assertIsNone(status_none.document_upload_description.raw_data)
