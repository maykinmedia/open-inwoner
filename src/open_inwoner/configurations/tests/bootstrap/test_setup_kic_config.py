import tempfile

from django.conf import settings
from django.test import TestCase, override_settings

import requests
import requests_mock
from django_setup_configuration.exceptions import SelfTestFailed
from simple_certmanager.constants import CertificateTypes

from open_inwoner.openklant.models import OpenKlantConfig

from ...bootstrap.kic import (
    ContactmomentenAPIConfigurationStep,
    KICAPIsConfigurationStep,
    KlantenAPIConfigurationStep,
)

KLANTEN_SERVICE_API_ROOT = "https://openklant.local/klanten/api/v1/"
CONTACTMOMENTEN_SERVICE_API_ROOT = "https://openklant.local/contactmomenten/api/v1/"

PUBLIC_CERT_FILE = tempfile.NamedTemporaryFile()

with open(PUBLIC_CERT_FILE.name, "w") as f:
    f.write("cert")


@override_settings(
    OIP_ORGANIZATION="Maykin",
    KIC_CONFIG_ENABLE=True,
    KIC_SERVER_CERTIFICATE_LABEL="KIC services server certificate",
    KIC_SERVER_CERTIFICATE_TYPE=CertificateTypes.cert_only,
    KIC_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE=PUBLIC_CERT_FILE.name,
    KIC_KLANTEN_SERVICE_API_ROOT=KLANTEN_SERVICE_API_ROOT,
    KIC_KLANTEN_SERVICE_API_CLIENT_ID="open-inwoner-test",
    KIC_KLANTEN_SERVICE_API_SECRET="klanten-secret",
    KIC_CONTACTMOMENTEN_SERVICE_API_ROOT=CONTACTMOMENTEN_SERVICE_API_ROOT,
    KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID="open-inwoner-test",
    KIC_CONTACTMOMENTEN_SERVICE_API_SECRET="contactmomenten-secret",
    KIC_REGISTER_EMAIL="admin@oip.org",
    KIC_REGISTER_CONTACT_MOMENT=True,
    KIC_REGISTER_BRONORGANISATIE_RSIN="837194569",
    KIC_REGISTER_CHANNEL="email",
    KIC_REGISTER_TYPE="bericht",
    KIC_REGISTER_EMPLOYEE_ID="1234",
    KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER=True,
)
class KICConfigurationTests(TestCase):
    def test_configure(self):
        KlantenAPIConfigurationStep().configure()
        ContactmomentenAPIConfigurationStep().configure()
        configuration = KICAPIsConfigurationStep()

        configuration.configure()

        config = OpenKlantConfig.get_solo()
        klanten_service = config.klanten_service
        contactmomenten_service = config.contactmomenten_service

        # certificates
        klanten_cert = klanten_service.server_certificate.public_certificate
        contactmomenten_cert = (
            contactmomenten_service.server_certificate.public_certificate
        )

        self.assertEqual(
            klanten_service.server_certificate.label, "KIC services server certificate"
        )
        self.assertTrue(klanten_cert.path.startswith(settings.PRIVATE_MEDIA_ROOT))
        self.assertEqual(klanten_cert.file.read(), b"cert")
        self.assertEqual(
            klanten_service.server_certificate.label, "KIC services server certificate"
        )
        self.assertTrue(
            contactmomenten_cert.path.startswith(settings.PRIVATE_MEDIA_ROOT)
        )
        self.assertEqual(contactmomenten_cert.file.read(), b"cert")

        # other settings
        self.assertEqual(klanten_service.api_root, KLANTEN_SERVICE_API_ROOT)
        self.assertEqual(klanten_service.client_id, "open-inwoner-test")
        self.assertEqual(klanten_service.secret, "klanten-secret")
        self.assertEqual(
            contactmomenten_service.api_root, CONTACTMOMENTEN_SERVICE_API_ROOT
        )
        self.assertEqual(contactmomenten_service.client_id, "open-inwoner-test")
        self.assertEqual(contactmomenten_service.secret, "contactmomenten-secret")

        self.assertEqual(config.register_email, "admin@oip.org")
        self.assertEqual(config.register_contact_moment, True)
        self.assertEqual(config.register_bronorganisatie_rsin, "837194569")
        self.assertEqual(config.register_channel, "email")
        self.assertEqual(config.register_type, "bericht")
        self.assertEqual(config.register_employee_id, "1234")
        self.assertEqual(config.use_rsin_for_innNnpId_query_parameter, True)

    @override_settings(
        OIP_ORGANIZATION=None,
        KIC_CONFIG_ENABLE=True,
        KIC_REGISTER_EMAIL=None,
        KIC_REGISTER_CONTACT_MOMENT=None,
        KIC_REGISTER_BRONORGANISATIE_RSIN=None,
        KIC_REGISTER_CHANNEL=None,
        KIC_REGISTER_TYPE=None,
        KIC_REGISTER_EMPLOYEE_ID=None,
        KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER=None,
    )
    def test_configure_use_defaults(self):
        KlantenAPIConfigurationStep().configure()
        ContactmomentenAPIConfigurationStep().configure()
        configuration = KICAPIsConfigurationStep()

        configuration.configure()

        config = OpenKlantConfig.get_solo()
        klanten_service = config.klanten_service
        contactmomenten_service = config.contactmomenten_service

        self.assertEqual(klanten_service.api_root, KLANTEN_SERVICE_API_ROOT)
        self.assertEqual(klanten_service.client_id, "open-inwoner-test")
        self.assertEqual(klanten_service.secret, "klanten-secret")
        self.assertEqual(
            contactmomenten_service.api_root, CONTACTMOMENTEN_SERVICE_API_ROOT
        )
        self.assertEqual(contactmomenten_service.client_id, "open-inwoner-test")
        self.assertEqual(contactmomenten_service.secret, "contactmomenten-secret")

        self.assertEqual(config.register_email, "")
        self.assertEqual(config.register_contact_moment, False)
        self.assertEqual(config.register_bronorganisatie_rsin, "")
        self.assertEqual(config.register_channel, "contactformulier")
        self.assertEqual(config.register_type, "Melding")
        self.assertEqual(config.register_employee_id, "")
        self.assertEqual(config.use_rsin_for_innNnpId_query_parameter, False)

    @requests_mock.Mocker()
    @override_settings(KIC_CONFIG_ENABLE=True)
    def test_configuration_check_ok(self, m):
        KlantenAPIConfigurationStep().configure()
        ContactmomentenAPIConfigurationStep().configure()
        configuration = KICAPIsConfigurationStep()

        configuration.configure()

        m.get(f"{KLANTEN_SERVICE_API_ROOT}klanten", json=[])
        m.get(f"{CONTACTMOMENTEN_SERVICE_API_ROOT}contactmomenten", json=[])

        configuration.test_configuration()

        status_request, zaaktype_request = m.request_history

        self.assertEqual(
            status_request.url,
            f"{KLANTEN_SERVICE_API_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=000000000",
        )
        self.assertEqual(
            zaaktype_request.url,
            f"{CONTACTMOMENTEN_SERVICE_API_ROOT}contactmomenten?identificatie=00000",
        )

    @requests_mock.Mocker()
    @override_settings(KIC_CONFIG_ENABLE=True)
    def test_configuration_check_failures(self, m):
        KlantenAPIConfigurationStep().configure()
        ContactmomentenAPIConfigurationStep().configure()
        configuration = KICAPIsConfigurationStep()
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
                m.get(f"{KLANTEN_SERVICE_API_ROOT}klanten", **mock_config)

                with self.assertRaises(SelfTestFailed):
                    configuration.test_configuration()

    @override_settings(KIC_CONFIG_ENABLE=True)
    def test_is_configured(self):
        configs = [
            KlantenAPIConfigurationStep(),
            ContactmomentenAPIConfigurationStep(),
            KICAPIsConfigurationStep(),
        ]
        for config in configs:
            with self.subTest(config=config.verbose_name):
                self.assertFalse(config.is_configured())

                config.configure()

                self.assertTrue(config.is_configured())

    @override_settings(KIC_CONFIG_ENABLE=False)
    def test_disable_kic_config(self):
        KlantenAPIConfigurationStep().configure()
        ContactmomentenAPIConfigurationStep().configure()
        configuration = KICAPIsConfigurationStep()
        configuration.configure()

        self.assertFalse(configuration.is_configured())
