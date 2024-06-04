from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.tests.test_migrations import TestMigrations


class TestMultiZGWBackendMigrations(TestMigrations):
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
