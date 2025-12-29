from django.db import DataError
from django.test import tag

from zgw_consumers.constants import APITypes

from open_inwoner.mijn_aanvragen.tests.factories import (
    ServiceFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.utils.tests.test_migrations import (
    TestFailingMigrations,
    TestSuccessfulMigrations,
)


@tag("migrations")
class TestMultiZGWBackendMigrations(TestSuccessfulMigrations):
    migrate_from = "0047_delete_statustranslation"
    migrate_to = "0051_drop_root_zgw_fields"
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")
        Service = apps.get_model("zgw_consumers", "Service")

        self.catalogi_service = ServiceFactory(api_type=APITypes.ztc)
        self.zaken_service = ServiceFactory(api_type=APITypes.zrc)
        self.documenten_service = ServiceFactory(api_type=APITypes.drc)
        self.forms_service = ServiceFactory(api_type=APITypes.orc)

        # Note we have to refetch the service instances here: the factories
        # create models that differ from the between-migration models
        # expected by this OpenZaakConfig
        OpenZaakConfig.objects.create(
            zaak_service=Service.objects.get(id=self.zaken_service.id),
            catalogi_service=Service.objects.get(id=self.catalogi_service.id),
            document_service=Service.objects.get(id=self.documenten_service.id),
            form_service=Service.objects.get(id=self.forms_service.id),
        )

    def test_migration_0048_to_0051_multi_zgw_backend(self):
        ZGWApiGroupConfig = self.apps.get_model("openzaak", "ZGWApiGroupConfig")
        OpenZaakConfig = self.apps.get_model("openzaak", "OpenZaakConfig")

        config = OpenZaakConfig.objects.get()
        with self.assertRaises(
            AttributeError, msg="Root-level service fields should be gone"
        ):
            for field in (
                "zaak_service",
                "catalogi_service",
                "document_service",
                "form_service",
            ):
                getattr(config, field)

        value = list(
            ZGWApiGroupConfig.objects.values_list(
                "zrc_service__id",
                "drc_service__id",
                "ztc_service__id",
                "form_service__id",
            )
        )
        expected = [
            (
                self.zaken_service.id,
                self.documenten_service.id,
                self.catalogi_service.id,
                self.forms_service.id,
            )
        ]

        self.assertEqual(
            value,
            expected,
            msg="Service config should have been moved to a new ZGWApiGroupConfig",
        )


class RequiredServiceToCatalogusConfigMigrationsTestCase:
    migrate_from = "0051_drop_root_zgw_fields"
    migrate_to = "0052_add_catalogusconfig_service"
    app = "openzaak"

    def setUp(self):
        self.api_group_config = ZGWApiGroupConfigFactory()  # Not affected by migrations
        super().setUp()


@tag("migrations")
class TestRequiredCatalogusConfigServiceHappyPath(
    RequiredServiceToCatalogusConfigMigrationsTestCase, TestSuccessfulMigrations
):
    def setUpBeforeMigration(self, apps):
        CatalogusConfig = apps.get_model("openzaak", "CatalogusConfig")
        CatalogusConfig.objects.create(
            url="https://foobar.com", domein="foo", rsin="foo"
        )

    def test_migration_0051_to_0052_sets_service_from_only_api_group_config(self):
        CatalogusConfig = self.apps.get_model("openzaak", "CatalogusConfig")
        catalogus_config = CatalogusConfig.objects.all().get()

        self.assertEqual(
            catalogus_config.service.pk,
            self.api_group_config.ztc_service.pk,
        )


@tag("migrations")
class TestRequiredCatalogusConfigServiceUnhappyPath(
    RequiredServiceToCatalogusConfigMigrationsTestCase, TestFailingMigrations
):
    def setUpBeforeMigration(self, apps):
        super().setUpBeforeMigration(apps)

        # Create another API Group Config to simulate ambiguous service resolution
        ZGWApiGroupConfig = apps.get_model("openzaak", "ZGWApiGroupConfig")
        Service = apps.get_model("zgw_consumers", "Service")
        OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")
        CatalogusConfig = apps.get_model("openzaak", "CatalogusConfig")

        CatalogusConfig = apps.get_model("openzaak", "CatalogusConfig")
        CatalogusConfig.objects.create(
            url="https://foobar.com", domein="foo", rsin="foo"
        )

        catalogi_service = ServiceFactory(api_type=APITypes.ztc)
        zaken_service = ServiceFactory(api_type=APITypes.zrc)
        documenten_service = ServiceFactory(api_type=APITypes.drc)
        forms_service = ServiceFactory(api_type=APITypes.orc)

        # Note we have to refetch the service instances here: the factories
        # create models that differ from the between-migration models
        # expected by this OpenZaakConfig
        ZGWApiGroupConfig.objects.create(
            open_zaak_config=OpenZaakConfig.objects.get(
                id=self.api_group_config.open_zaak_config.id
            ),
            zrc_service=Service.objects.get(id=zaken_service.id),
            ztc_service=Service.objects.get(id=catalogi_service.id),
            drc_service=Service.objects.get(id=documenten_service.id),
            form_service=Service.objects.get(id=forms_service.id),
        )

    def test_migration_0051_to_0052_raises_for_multiple_api_groups(self):
        with self.assertRaises(DataError) as cm:
            self.attempt_migration()

        self.assertEqual(
            str(cm.exception),
            "Attempted to set CatalogusConfig.service using ZGWApiGroupConfig, but there"
            " are multiple instances configured. Please (temporarily) ensure you have only a single"
            " ZGWApiGroupConfig configured, then run this migration again.",
        )


@tag("migrations")
class TestMakeZaakTypeConfigCatalogusRequired(TestFailingMigrations):
    migrate_from = "0052_add_catalogusconfig_service"
    migrate_to = "0053_zaaktypeconfig_catalogus_is_required"
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        ZaakTypeConfig = apps.get_model("openzaak", "ZaakTypeConfig")
        ZaakTypeConfig.objects.create(urls=[], catalogus=None, identificatie="foobar")

    def test_migration_0051_to_0052_raises_with_descriptive_exception_message(self):
        with self.assertRaises(DataError) as cm:
            self.attempt_migration()

        self.assertEqual(
            str(cm.exception),
            "Your database contains 1 ZaakTypeConfig row(s) with a missing `catalogus` field."
            " This field is now required: please manually update all the affected rows or re-sync"
            " your ZGW objects to ensure the field is included.",
        )


@tag("migrations")
class TestZGWApiGroupServicesRequiredFailingMigration(TestFailingMigrations):
    migrate_from = "0053_zaaktypeconfig_catalogus_is_required"
    migrate_to = "0054_zgw_api_group_requires_most_services"
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")
        ZGWApiGroupConfig = apps.get_model("openzaak", "ZGWApiGroupConfig")
        config = OpenZaakConfig.objects.create()
        ZGWApiGroupConfig.objects.create(
            open_zaak_config=config,
            zrc_service=None,
            drc_service=None,
            ztc_service=None,
            form_service=None,
        )

    def test_migration_0053_to_0054_raises_with_descriptive_exception_message(self):
        with self.assertRaises(DataError) as cm:
            self.attempt_migration()

        self.assertEqual(
            str(cm.exception),
            "Your database contains 1 ZGWApiGroupConfig row(s) with missing ztc, drc,"
            " or ztc service fields. All these fields are now required, with the exception of"
            " your form field. Please manually update all the affected rows",
        )


@tag("migrations")
class TestZGWApiGroupServicesRequiredSuccessfulMigration(TestSuccessfulMigrations):
    migrate_from = "0053_zaaktypeconfig_catalogus_is_required"
    migrate_to = "0054_zgw_api_group_requires_most_services"
    extra_migrate_from = [("zgw_consumers", "0019_alter_service_uuid")]
    app = "openzaak"

    def setUpBeforeMigration(self, apps):
        OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")
        config = OpenZaakConfig.objects.create()
        ZGWApiGroupConfig = apps.get_model("openzaak", "ZGWApiGroupConfig")
        Service = apps.get_model("zgw_consumers", "Service")
        ZGWApiGroupConfig.objects.create(
            open_zaak_config=config,
            name="The Group",
            zrc_service=Service.objects.create(
                api_root="http://foobar/zrc", api_type=APITypes.zrc
            ),
            drc_service=Service.objects.create(
                api_root="http://foobar/drc", api_type=APITypes.drc
            ),
            ztc_service=Service.objects.create(
                api_root="http://foobar/ztc", api_type=APITypes.ztc
            ),
            form_service=None,  # Optional, should not raise
        )

    def test_migration_leaves_config_models_unchanged(self):
        ZGWApiGroupConfig = self.apps.get_model("openzaak", "ZGWApiGroupConfig")
        Service = self.apps.get_model("zgw_consumers", "Service")
        self.assertEqual(
            list(ZGWApiGroupConfig.objects.values_list("name", flat=True)),
            ["The Group"],
        )
        self.assertEqual(
            list(Service.objects.values_list("api_root", "api_type")),
            [
                ("http://foobar/zrc", "zrc"),
                ("http://foobar/drc", "drc"),
                ("http://foobar/ztc", "ztc"),
            ],
        )


@tag("migrations")
class StatusTypeDescriptionsMigrationTest(TestSuccessfulMigrations):
    """Tests the migration of ZaakTypeStatusTypeConfig descriptions to ProsemirrorModelFields."""

    migrate_from = "0069_parameter_spelling"
    migrate_to = "0072_zaaktypestatustypeconfig_description_schema_2"
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

        # Create statustype config with historical model
        ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            omschrijving="Test Statustype",
            statustekst="Test Statustekst",
            description="**Bold text** and _italic text_ with a [link](https://example.com)",
        )

    def test_description_migration(self):
        ZaakTypeStatusTypeConfig = self.apps.get_model(
            "openzaak", "ZaakTypeStatusTypeConfig"
        )

        statustype_config = ZaakTypeStatusTypeConfig.objects.first()

        expected_html = '<p><strong>Bold text</strong> and <em>italic text</em> with a <a href="https://example.com">link</a></p>'
        self.assertEqual(statustype_config.description.html, expected_html)

        # Ensure the temporary field was removed
        self.assertFalse(hasattr(statustype_config, "description_tmp"))


@tag("migrations")
class StatusTypeDocUploadDescriptionMigrationTest(TestSuccessfulMigrations):
    """Tests the migration of ZaakTypeStatusTypeConfig document_upload_description to ProsemirrorModelFields."""

    migrate_from = "0072_zaaktypestatustypeconfig_description_schema_2"
    migrate_to = "0075_zaaktypestatustypeconfig_doc_upload_description_schema_2"
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

        # Create statustype config with historical model
        ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            omschrijving="Test Statustype",
            statustekst="Test Statustekst",
            document_upload_description="**Upload instructions** with _formatting_ and a [link](https://example.com/upload-help)",
        )

    def test_document_upload_description_migration(self):
        ZaakTypeStatusTypeConfig = self.apps.get_model(
            "openzaak", "ZaakTypeStatusTypeConfig"
        )

        statustype_config = ZaakTypeStatusTypeConfig.objects.first()

        expected_html = '<p><strong>Upload instructions</strong> with <em>formatting</em> and a <a href="https://example.com/upload-help">link</a></p>'
        self.assertEqual(
            statustype_config.document_upload_description.html, expected_html
        )

        # Ensure the temporary field was removed
        self.assertFalse(hasattr(statustype_config, "document_upload_description_tmp"))
