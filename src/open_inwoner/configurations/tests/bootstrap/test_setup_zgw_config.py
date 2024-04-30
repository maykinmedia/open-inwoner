from django.test import TestCase, override_settings
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_setup_configuration.exceptions import SelfTestFailed
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    generate_default_file_extensions,
)

from ...bootstrap.zgw import (
    CatalogiAPIConfigurationStep,
    DocumentenAPIConfigurationStep,
    FormulierenAPIConfigurationStep,
    ZakenAPIConfigurationStep,
    ZGWAPIsConfigurationStep,
)

ZAAK_SERVICE_API_ROOT = "https://openzaak.local/zaken/api/v1/"
CATALOGI_SERVICE_API_ROOT = "https://openzaak.local/catalogi/api/v1/"
DOCUMENTEN_SERVICE_API_ROOT = "https://openzaak.local/documenten/api/v1/"
FORM_SERVICE_API_ROOT = "https://esuite.local.net/formulieren-provider/api/v1/"


@override_settings(
    OIP_ORGANIZATION="Maykin",
    ZGW_ZAAK_SERVICE_API_ROOT=ZAAK_SERVICE_API_ROOT,
    ZGW_ZAAK_SERVICE_API_CLIENT_ID="open-inwoner-test",
    ZGW_ZAAK_SERVICE_API_SECRET="zaken-secret",
    ZGW_CATALOGI_SERVICE_API_ROOT=CATALOGI_SERVICE_API_ROOT,
    ZGW_CATALOGI_SERVICE_API_CLIENT_ID="open-inwoner-test",
    ZGW_CATALOGI_SERVICE_API_SECRET="catalogi-secret",
    ZGW_DOCUMENTEN_SERVICE_API_ROOT=DOCUMENTEN_SERVICE_API_ROOT,
    ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID="open-inwoner-test",
    ZGW_DOCUMENTEN_SERVICE_API_SECRET="documenten-secret",
    ZGW_FORM_SERVICE_API_ROOT=FORM_SERVICE_API_ROOT,
    ZGW_FORM_SERVICE_API_CLIENT_ID="open-inwoner-test",
    ZGW_FORM_SERVICE_API_SECRET="forms-secret",
    ZGW_ZAAK_MAX_CONFIDENTIALITY=VertrouwelijkheidsAanduidingen.vertrouwelijk,
    ZGW_DOCUMENT_MAX_CONFIDENTIALITY=VertrouwelijkheidsAanduidingen.zaakvertrouwelijk,
    ZGW_ACTION_REQUIRED_DEADLINE_DAYS=12,
    ZGW_ALLOWED_FILE_EXTENSIONS=[".pdf", ".txt"],
    ZGW_MIJN_AANVRAGEN_TITLE_TEXT="title text",
    ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN=True,
    ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN=True,
    ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE=True,
    ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN=True,
)
class ZGWConfigurationTests(TestCase):
    def test_configure(self):
        ZakenAPIConfigurationStep().configure()
        CatalogiAPIConfigurationStep().configure()
        DocumentenAPIConfigurationStep().configure()
        FormulierenAPIConfigurationStep().configure()
        configuration = ZGWAPIsConfigurationStep()

        configuration.configure()

        config = OpenZaakConfig.get_solo()
        zaak_service = config.zaak_service
        catalogi_service = config.catalogi_service
        document_service = config.document_service
        form_service = config.form_service

        self.assertEqual(zaak_service.api_root, ZAAK_SERVICE_API_ROOT)
        self.assertEqual(zaak_service.client_id, "open-inwoner-test")
        self.assertEqual(zaak_service.secret, "zaken-secret")
        self.assertEqual(catalogi_service.api_root, CATALOGI_SERVICE_API_ROOT)
        self.assertEqual(catalogi_service.client_id, "open-inwoner-test")
        self.assertEqual(catalogi_service.secret, "catalogi-secret")
        self.assertEqual(document_service.api_root, DOCUMENTEN_SERVICE_API_ROOT)
        self.assertEqual(document_service.client_id, "open-inwoner-test")
        self.assertEqual(document_service.secret, "documenten-secret")
        self.assertEqual(form_service.api_root, FORM_SERVICE_API_ROOT)
        self.assertEqual(form_service.client_id, "open-inwoner-test")
        self.assertEqual(form_service.secret, "forms-secret")

        self.assertEqual(
            config.zaak_max_confidentiality,
            VertrouwelijkheidsAanduidingen.vertrouwelijk,
        )
        self.assertEqual(
            config.document_max_confidentiality,
            VertrouwelijkheidsAanduidingen.zaakvertrouwelijk,
        )
        self.assertEqual(config.action_required_deadline_days, 12)
        self.assertEqual(config.allowed_file_extensions, [".pdf", ".txt"])
        self.assertEqual(config.title_text, "title text")
        self.assertEqual(config.enable_categories_filtering_with_zaken, True)
        self.assertEqual(config.skip_notification_statustype_informeren, True)
        self.assertEqual(config.reformat_esuite_zaak_identificatie, True)
        self.assertEqual(config.fetch_eherkenning_zaken_with_rsin, True)

    @override_settings(
        OIP_ORGANIZATION=None,
        ZGW_ZAAK_MAX_CONFIDENTIALITY=None,
        ZGW_DOCUMENT_MAX_CONFIDENTIALITY=None,
        ZGW_ACTION_REQUIRED_DEADLINE_DAYS=None,
        ZGW_ALLOWED_FILE_EXTENSIONS=None,
        ZGW_MIJN_AANVRAGEN_TITLE_TEXT=None,
        ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN=None,
        ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN=None,
        ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE=None,
        ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN=None,
    )
    def test_configure_use_defaults(self):
        ZakenAPIConfigurationStep().configure()
        CatalogiAPIConfigurationStep().configure()
        DocumentenAPIConfigurationStep().configure()
        FormulierenAPIConfigurationStep().configure()
        configuration = ZGWAPIsConfigurationStep()

        configuration.configure()

        config = OpenZaakConfig.get_solo()
        zaak_service = config.zaak_service
        catalogi_service = config.catalogi_service
        document_service = config.document_service
        form_service = config.form_service

        self.assertEqual(zaak_service.api_root, ZAAK_SERVICE_API_ROOT)
        self.assertEqual(zaak_service.client_id, "open-inwoner-test")
        self.assertEqual(zaak_service.secret, "zaken-secret")
        self.assertEqual(catalogi_service.api_root, CATALOGI_SERVICE_API_ROOT)
        self.assertEqual(catalogi_service.client_id, "open-inwoner-test")
        self.assertEqual(catalogi_service.secret, "catalogi-secret")
        self.assertEqual(document_service.api_root, DOCUMENTEN_SERVICE_API_ROOT)
        self.assertEqual(document_service.client_id, "open-inwoner-test")
        self.assertEqual(document_service.secret, "documenten-secret")
        self.assertEqual(form_service.api_root, FORM_SERVICE_API_ROOT)
        self.assertEqual(form_service.client_id, "open-inwoner-test")
        self.assertEqual(form_service.secret, "forms-secret")

        # Defaults should be used
        self.assertEqual(
            config.zaak_max_confidentiality, VertrouwelijkheidsAanduidingen.openbaar
        )
        self.assertEqual(
            config.document_max_confidentiality, VertrouwelijkheidsAanduidingen.openbaar
        )
        self.assertEqual(config.action_required_deadline_days, 15)
        self.assertEqual(
            config.allowed_file_extensions, generate_default_file_extensions()
        )
        self.assertEqual(
            config.title_text,
            _("Hier vindt u een overzicht van al uw lopende en afgeronde aanvragen."),
        )
        self.assertEqual(config.enable_categories_filtering_with_zaken, False)
        self.assertEqual(config.skip_notification_statustype_informeren, False)
        self.assertEqual(config.reformat_esuite_zaak_identificatie, False)
        self.assertEqual(config.fetch_eherkenning_zaken_with_rsin, False)

    @requests_mock.Mocker()
    def test_configuration_check_ok(self, m):
        ZakenAPIConfigurationStep().configure()
        CatalogiAPIConfigurationStep().configure()
        DocumentenAPIConfigurationStep().configure()
        FormulierenAPIConfigurationStep().configure()
        configuration = ZGWAPIsConfigurationStep()

        configuration.configure()

        m.get(f"{ZAAK_SERVICE_API_ROOT}statussen", json=[])
        m.get(f"{CATALOGI_SERVICE_API_ROOT}zaaktypen", json=[])
        m.get(f"{DOCUMENTEN_SERVICE_API_ROOT}objectinformatieobjecten", json=[])
        m.get(
            f"{FORM_SERVICE_API_ROOT}openstaande-inzendingen",
            json=[],
        )

        configuration.test_configuration()

        (
            status_request,
            zaaktype_request,
            oio_request,
            inzendingen_request,
        ) = m.request_history

        self.assertEqual(status_request.url, f"{ZAAK_SERVICE_API_ROOT}statussen")
        self.assertEqual(zaaktype_request.url, f"{CATALOGI_SERVICE_API_ROOT}zaaktypen")
        self.assertEqual(
            oio_request.url, f"{DOCUMENTEN_SERVICE_API_ROOT}objectinformatieobjecten"
        )
        self.assertEqual(
            inzendingen_request.url,
            f"{FORM_SERVICE_API_ROOT}openstaande-inzendingen?bsn=000000000",
        )

    @requests_mock.Mocker()
    def test_configuration_check_failures(self, m):
        ZakenAPIConfigurationStep().configure()
        CatalogiAPIConfigurationStep().configure()
        DocumentenAPIConfigurationStep().configure()
        FormulierenAPIConfigurationStep().configure()
        configuration = ZGWAPIsConfigurationStep()

        configuration.configure()

        mock_kwargs = (
            {"exc": requests.ConnectTimeout},
            {"exc": requests.ConnectionError},
            {"status_code": 404},
            {"status_code": 403},
            {"status_code": 500},
        )
        for mock_config in mock_kwargs:
            with self.subTest(mock=mock_config):
                m.get(f"{ZAAK_SERVICE_API_ROOT}statussen", **mock_config)

                with self.assertRaises(SelfTestFailed):
                    configuration.test_configuration()

    def test_is_configured(self):
        configs = [
            ZakenAPIConfigurationStep(),
            CatalogiAPIConfigurationStep(),
            DocumentenAPIConfigurationStep(),
            FormulierenAPIConfigurationStep(),
            ZGWAPIsConfigurationStep(),
        ]
        for config in configs:
            with self.subTest(config=config.verbose_name):
                self.assertFalse(config.is_configured())

                config.configure()

                self.assertTrue(config.is_configured())
