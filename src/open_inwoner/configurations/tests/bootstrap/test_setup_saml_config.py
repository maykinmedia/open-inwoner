from unittest.mock import patch

from django.test import TestCase

from digid_eherkenning.models import (
    ConfigCertificate,
    DigidConfiguration,
    EherkenningConfiguration,
)
from django_setup_configuration.exceptions import (
    ConfigurationRunFailed,
    PrerequisiteFailed,
)
from django_setup_configuration.test_utils import execute_single_step
from privates.test import temp_private_root
from simple_certmanager.models import Certificate

from open_inwoner.configurations.bootstrap.saml import (
    DigiDSAMLConfigurationStep,
    eHerkenningSAMLConfigurationStep,
)
from open_inwoner.kvk.tests.factories import TEST_FILES

PUBLIC_CERT = str(TEST_FILES / "public_cert.crt")
PRIVATE_KEY = str(TEST_FILES / "private_key.key")

CERTIFICATE = {
    "label": "Test SAML certificate",
    "type": "key_pair",
    "public_certificate": PUBLIC_CERT,
    "private_key": PRIVATE_KEY,
}

DIGID_SETTINGS = {
    "entity_id": "https://example.org/digid/metadata",
    "base_url": "https://example.org",
    "service_name": "Test DigiD",
    "service_description": "Test DigiD description",
    "metadata_file_source": "https://idp.example.org/digid/metadata",
}

EHERKENNING_SETTINGS = {
    "entity_id": "https://example.org/eherkenning/metadata",
    "base_url": "https://example.org",
    "service_name": "Test eHerkenning",
    "service_description": "Test eHerkenning description",
    "metadata_file_source": "https://idp.example.org/eherkenning/metadata",
    "oin": "12345678901234567890",
    "privacy_policy": "https://example.org/privacy",
    "makelaar_id": "09876543210987654321",
    "service_description_url": "https://example.org/service-description",
    "eh_service_uuid": "53a3a1b4-eab3-41dc-a619-143237189fac",
    "eh_service_instance_uuid": "fe5f47ea-2781-497f-9e82-3fbe3b960e19",
    "eidas_service_uuid": "9ff00e2b-149d-4fd1-9578-af91c966b309",
    "eidas_service_instance_uuid": "ae57d248-db9a-491b-8fb0-f88f92131f96",
}


def mock_metadata_fetch():
    """
    `BaseConfiguration.save()` fetches and parses metadata from
    `metadata_file_source` over the network whenever that field is set. Patch
    it out so the test suite never makes a real HTTP call.
    """
    return patch(
        "digid_eherkenning.models.base.BaseConfiguration.process_metadata_from_xml_source",
        return_value=({"entityId": "https://idp.example.org/metadata"}, b"<xml/>"),
    )


@temp_private_root()
class DigiDSAMLConfigurationStepTests(TestCase):
    def test_configure_with_certificate_sets_fields_and_certificate(self):
        with mock_metadata_fetch():
            execute_single_step(
                DigiDSAMLConfigurationStep,
                object_source={
                    "digid_saml_config_enable": True,
                    "digid_saml_config": {**DIGID_SETTINGS, "certificate": CERTIFICATE},
                },
            )

        config = DigidConfiguration.get_solo()
        self.assertEqual(config.entity_id, DIGID_SETTINGS["entity_id"])
        self.assertEqual(config.base_url, DIGID_SETTINGS["base_url"])
        self.assertEqual(config.service_name, DIGID_SETTINGS["service_name"])
        self.assertEqual(
            config.service_description, DIGID_SETTINGS["service_description"]
        )

        certificate = Certificate.objects.get(label=CERTIFICATE["label"])
        self.assertTrue(certificate.public_certificate)
        self.assertTrue(certificate.private_key)
        self.assertTrue(
            ConfigCertificate.objects.filter(
                config_type=DigidConfiguration._as_config_type(),
                certificate=certificate,
            ).exists()
        )

    def test_certificate_provisioning_is_idempotent(self):
        with mock_metadata_fetch():
            for _ in range(2):
                execute_single_step(
                    DigiDSAMLConfigurationStep,
                    object_source={
                        "digid_saml_config_enable": True,
                        "digid_saml_config": {
                            **DIGID_SETTINGS,
                            "certificate": CERTIFICATE,
                        },
                    },
                )

        self.assertEqual(
            Certificate.objects.filter(label=CERTIFICATE["label"]).count(), 1
        )

    def test_rerun_with_a_different_value_overwrites_the_admin_edit(self):
        """
        Simulates an admin editing a field after it was bootstrapped:
        re-running the step overwrites that edit. The certificate, attached
        once, is left alone on the second run.
        """
        with mock_metadata_fetch():
            execute_single_step(
                DigiDSAMLConfigurationStep,
                object_source={
                    "digid_saml_config_enable": True,
                    "digid_saml_config": {**DIGID_SETTINGS, "certificate": CERTIFICATE},
                },
            )
            config = DigidConfiguration.get_solo()
            config.service_name = "Admin-edited name"
            config.save()

            execute_single_step(
                DigiDSAMLConfigurationStep,
                object_source={
                    "digid_saml_config_enable": True,
                    "digid_saml_config": DIGID_SETTINGS,
                },
            )

        config.refresh_from_db()
        self.assertEqual(config.service_name, DIGID_SETTINGS["service_name"])
        self.assertEqual(Certificate.objects.count(), 1)

    def test_no_certificate_ever_configured_raises_configuration_run_failed(self):
        with self.assertRaises(ConfigurationRunFailed):
            execute_single_step(
                DigiDSAMLConfigurationStep,
                object_source={
                    "digid_saml_config_enable": True,
                    "digid_saml_config": DIGID_SETTINGS,
                },
            )

    def test_unreadable_certificate_file_raises_configuration_run_failed(self):
        with self.assertRaises(ConfigurationRunFailed):
            execute_single_step(
                DigiDSAMLConfigurationStep,
                object_source={
                    "digid_saml_config_enable": True,
                    "digid_saml_config": {
                        **DIGID_SETTINGS,
                        "certificate": {
                            **CERTIFICATE,
                            "public_certificate": "/does/not/exist.pem",
                        },
                    },
                },
            )
        self.assertFalse(Certificate.objects.exists())


@temp_private_root()
class eHerkenningSAMLConfigurationStepTests(TestCase):
    def test_configure_with_certificate_sets_fields_and_certificate(self):
        with mock_metadata_fetch():
            execute_single_step(
                eHerkenningSAMLConfigurationStep,
                object_source={
                    "eherkenning_saml_config_enable": True,
                    "eherkenning_saml_config": {
                        **EHERKENNING_SETTINGS,
                        "certificate": CERTIFICATE,
                    },
                },
            )

        config = EherkenningConfiguration.get_solo()
        self.assertEqual(config.entity_id, EHERKENNING_SETTINGS["entity_id"])
        self.assertEqual(config.oin, EHERKENNING_SETTINGS["oin"])
        self.assertEqual(config.makelaar_id, EHERKENNING_SETTINGS["makelaar_id"])

        certificate = Certificate.objects.get(label=CERTIFICATE["label"])
        self.assertTrue(
            ConfigCertificate.objects.filter(
                config_type=EherkenningConfiguration._as_config_type(),
                certificate=certificate,
            ).exists()
        )

    def test_rerun_with_the_same_uuids_keeps_them_stable(self):
        """
        The service/instance UUIDs are registered in external catalogues, so
        re-running with the same pinned values must not change them -- unlike
        every other field, they have no default to fall back on if omitted.
        """
        with mock_metadata_fetch():
            for _ in range(2):
                execute_single_step(
                    eHerkenningSAMLConfigurationStep,
                    object_source={
                        "eherkenning_saml_config_enable": True,
                        "eherkenning_saml_config": {
                            **EHERKENNING_SETTINGS,
                            "certificate": CERTIFICATE,
                        },
                    },
                )

        config = EherkenningConfiguration.get_solo()
        self.assertEqual(
            str(config.eh_service_uuid), EHERKENNING_SETTINGS["eh_service_uuid"]
        )

    def test_missing_uuid_raises_prerequisite_failed(self):
        settings_without_uuid = {
            k: v for k, v in EHERKENNING_SETTINGS.items() if k != "eh_service_uuid"
        }
        with self.assertRaises(PrerequisiteFailed):
            execute_single_step(
                eHerkenningSAMLConfigurationStep,
                object_source={
                    "eherkenning_saml_config_enable": True,
                    "eherkenning_saml_config": {
                        **settings_without_uuid,
                        "certificate": CERTIFICATE,
                    },
                },
            )

    def test_no_certificate_ever_configured_raises_configuration_run_failed(self):
        with self.assertRaises(ConfigurationRunFailed):
            execute_single_step(
                eHerkenningSAMLConfigurationStep,
                object_source={
                    "eherkenning_saml_config_enable": True,
                    "eherkenning_saml_config": EHERKENNING_SETTINGS,
                },
            )
