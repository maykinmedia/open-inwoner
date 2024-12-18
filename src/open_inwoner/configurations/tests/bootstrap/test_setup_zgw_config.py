from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import (
    ConfigurationRunFailed,
    PrerequisiteFailed,
)
from django_setup_configuration.test_utils import execute_single_step
from privates.test import temp_private_root
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.zgw import OpenZaakConfigurationStep
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory

ZAAK_SERVICE_API_ROOT = "https://openzaak.local/zaken/api/v1/"
CATALOGI_SERVICE_API_ROOT = "https://openzaak.local/catalogi/api/v1/"
DOCUMENTEN_SERVICE_API_ROOT = "https://openzaak.local/documenten/api/v1/"
FORM_SERVICE_API_ROOT = "https://esuite.local.net/formulieren-provider/api/v1/"


BASE_DIR = Path(__file__).parent / "files"
ZGW_API_STEP_YAML_FULL = str(BASE_DIR / "zgw_api_step_full.yaml")
ZGW_API_STEP_YAML_ZERO_GROUPS = str(BASE_DIR / "zgw_api_step_zero_groups.yaml")
ZGW_API_STEP_YAML_MISSING_GROUPS = str(BASE_DIR / "zgw_api_step_missing_groups.yaml")


@temp_private_root()
class ZGWConfigurationTests(TestCase):
    def setUp(self):
        self.zaak_service = ServiceFactory(
            api_type=APITypes.zrc, slug="zaak-api", api_root=ZAAK_SERVICE_API_ROOT
        )
        self.catalogi_service = ServiceFactory(
            api_type=APITypes.ztc,
            slug="catalogus-api",
            api_root=CATALOGI_SERVICE_API_ROOT,
        )
        self.document_service = ServiceFactory(
            api_type=APITypes.drc,
            slug="document-api",
            api_root=DOCUMENTEN_SERVICE_API_ROOT,
        )
        self.form_service = ServiceFactory(
            api_type=APITypes.orc, slug="form-api", api_root=FORM_SERVICE_API_ROOT
        )
        # Some other services
        for _ in range(10):
            ServiceFactory()

    def assert_openzaak_config_defaults(self):
        config = OpenZaakConfig.get_solo()
        self.assertIsNone(config.zaak_service)
        self.assertIsNone(config.catalogi_service)
        self.assertIsNone(config.document_service)
        self.assertIsNone(config.form_service)

        self.assertEqual(config.action_required_deadline_days, 15)
        self.assertEqual(
            config.allowed_file_extensions,
            [
                "bmp",
                "doc",
                "docx",
                "gif",
                "jpeg",
                "jpg",
                "msg",
                "pdf",
                "png",
                "ppt",
                "pptx",
                "rtf",
                "tiff",
                "txt",
                "vsd",
                "xls",
                "xlsx",
            ],
        )
        self.assertEqual(
            config.title_text,
            "Hier vindt u een overzicht van al uw lopende en afgeronde aanvragen.",
        )
        self.assertEqual(config.enable_categories_filtering_with_zaken, False)
        self.assertEqual(config.skip_notification_statustype_informeren, False)
        self.assertEqual(config.reformat_esuite_zaak_identificatie, False)
        self.assertEqual(config.fetch_eherkenning_zaken_with_rsin, False)

    def test_configure_full_sets_the_correct_fields(self):
        execute_single_step(
            OpenZaakConfigurationStep, yaml_source=ZGW_API_STEP_YAML_FULL
        )
        config = OpenZaakConfig.get_solo()

        zaak_service = config.zaak_service
        catalogi_service = config.catalogi_service
        document_service = config.document_service
        form_service = config.form_service

        self.assertEqual(zaak_service.api_root, ZAAK_SERVICE_API_ROOT)
        self.assertEqual(catalogi_service.api_root, CATALOGI_SERVICE_API_ROOT)
        self.assertEqual(document_service.api_root, DOCUMENTEN_SERVICE_API_ROOT)
        self.assertEqual(form_service.api_root, FORM_SERVICE_API_ROOT)

        self.assertEqual(
            config.zaak_max_confidentiality,
            VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.assertEqual(
            config.document_max_confidentiality,
            VertrouwelijkheidsAanduidingen.vertrouwelijk,
        )
        self.assertEqual(config.action_required_deadline_days, 1874)
        self.assertEqual(config.allowed_file_extensions, [".pdf", ".txt"])
        self.assertEqual(config.title_text, "title text from setup configuration")
        self.assertEqual(config.enable_categories_filtering_with_zaken, True)
        self.assertEqual(config.skip_notification_statustype_informeren, False)
        self.assertEqual(config.reformat_esuite_zaak_identificatie, True)
        self.assertEqual(config.fetch_eherkenning_zaken_with_rsin, False)

    def test_configure_raises_on_missing_groups(self):
        with self.assertRaises(PrerequisiteFailed):
            execute_single_step(
                OpenZaakConfigurationStep, yaml_source=ZGW_API_STEP_YAML_MISSING_GROUPS
            )

        self.assert_openzaak_config_defaults()

    def test_configure_raises_on_zero_groups(self):
        with self.assertRaises(ConfigurationRunFailed):
            execute_single_step(
                OpenZaakConfigurationStep, yaml_source=ZGW_API_STEP_YAML_ZERO_GROUPS
            )

        self.assert_openzaak_config_defaults()

    def test_configure_updates_existing_values_for_services(self):
        for attr in (
            "zaak",
            "document",
            "catalogus",
            "form",
        ):
            assert (
                Service.objects.filter(slug=f"{attr}-api").update(
                    api_root=f"http://an/updated/root/{attr}"
                )
                == 1
            )

        execute_single_step(
            OpenZaakConfigurationStep, yaml_source=ZGW_API_STEP_YAML_FULL
        )

        config = OpenZaakConfig.get_solo()

        self.assertEqual(config.zaak_service.api_root, "http://an/updated/root/zaak")
        self.assertEqual(
            config.catalogi_service.api_root, "http://an/updated/root/catalogus"
        )
        self.assertEqual(
            config.document_service.api_root, "http://an/updated/root/document"
        )
        self.assertEqual(config.form_service.api_root, "http://an/updated/root/form")
