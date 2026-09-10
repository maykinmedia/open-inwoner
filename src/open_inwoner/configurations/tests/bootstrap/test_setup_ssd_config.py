from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step

from open_inwoner.configurations.bootstrap.ssd import SSDConfigurationStep
from open_inwoner.soap.tests.factories import SoapServiceFactory
from open_inwoner.ssd.models import SSDConfig

SSD_SERVICE_URL = "http://ssd.internal/"

BASE_DIR = Path(__file__).parent / "files"
SSD_CONFIG_STEP_FULL_YAML = str(BASE_DIR / "ssd_config_step_full.yaml")
SSD_CONFIG_STEP_MINIMAL_YAML = str(BASE_DIR / "ssd_config_step_minimal.yaml")


class SSDConfigurationStepTest(TestCase):
    def test_configure_with_full_config(self):
        service = SoapServiceFactory(label="ssd-service", url=SSD_SERVICE_URL)

        execute_single_step(
            SSDConfigurationStep,
            yaml_source=SSD_CONFIG_STEP_FULL_YAML,
        )

        config = SSDConfig.get_solo()
        self.assertEqual(config.service, service)
        self.assertEqual(config.applicatie_naam, "Open Inwoner")
        self.assertEqual(config.bedrijfs_naam, "Open Inwoner")
        self.assertEqual(config.gemeentecode, "0000")

    def test_configure_with_minimal_config_leaves_omitted_fields_untouched(self):
        service = SoapServiceFactory(label="ssd-service", url=SSD_SERVICE_URL)

        config = SSDConfig.get_solo()
        config.applicatie_naam = "Existing application"
        config.bedrijfs_naam = "Existing company"
        config.gemeentecode = "1234"
        config.save()

        execute_single_step(
            SSDConfigurationStep,
            yaml_source=SSD_CONFIG_STEP_MINIMAL_YAML,
        )

        config = SSDConfig.get_solo()
        self.assertEqual(config.service, service)
        # not present in the minimal YAML, so left as they were
        self.assertEqual(config.applicatie_naam, "Existing application")
        self.assertEqual(config.bedrijfs_naam, "Existing company")
        self.assertEqual(config.gemeentecode, "1234")

    def test_configure_fails_with_nonexistent_service_identifier(self):
        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                SSDConfigurationStep,
                yaml_source=SSD_CONFIG_STEP_MINIMAL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Unable to retrieve SoapService with identifier `ssd-service`. Try "
            "first configuring the `soap_services_config` step.",
        )

    def test_configure_is_idempotent(self):
        service = SoapServiceFactory(label="ssd-service", url=SSD_SERVICE_URL)

        for _ in range(2):
            execute_single_step(
                SSDConfigurationStep,
                yaml_source=SSD_CONFIG_STEP_FULL_YAML,
            )

        config = SSDConfig.get_solo()
        self.assertEqual(config.service, service)
        self.assertEqual(config.applicatie_naam, "Open Inwoner")
