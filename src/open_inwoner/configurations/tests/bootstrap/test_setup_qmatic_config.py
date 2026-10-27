from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step
from zgw_consumers.constants import APITypes

from open_inwoner.configurations.bootstrap.qmatic import QmaticConfigurationStep
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.qmatic.models import QmaticConfig

QMATIC_API_ROOT = "http://qmatic.internal/"

BASE_DIR = Path(__file__).parent / "files"
QMATIC_CONFIG_STEP_FULL_YAML = str(BASE_DIR / "qmatic_config_step_full.yaml")
QMATIC_CONFIG_STEP_MINIMAL_YAML = str(BASE_DIR / "qmatic_config_step_minimal.yaml")


class QmaticConfigurationStepTest(TestCase):
    def test_configure_with_full_config(self):
        service = ServiceFactory(
            slug="qmatic-service", api_root=QMATIC_API_ROOT, api_type=APITypes.orc
        )

        execute_single_step(
            QmaticConfigurationStep,
            yaml_source=QMATIC_CONFIG_STEP_FULL_YAML,
        )

        config = QmaticConfig.get_solo()
        self.assertEqual(config.service, service)
        self.assertEqual(config.booking_base_url, "https://qmatic.local/afspraak/")

    def test_configure_with_minimal_config_leaves_omitted_fields_untouched(self):
        service = ServiceFactory(
            slug="qmatic-service", api_root=QMATIC_API_ROOT, api_type=APITypes.orc
        )

        config = QmaticConfig.get_solo()
        config.booking_base_url = "https://existing.example.com/"
        config.save()

        execute_single_step(
            QmaticConfigurationStep,
            yaml_source=QMATIC_CONFIG_STEP_MINIMAL_YAML,
        )

        config = QmaticConfig.get_solo()
        self.assertEqual(config.service, service)
        # not present in the minimal YAML, so left as it was
        self.assertEqual(config.booking_base_url, "https://existing.example.com/")

    def test_configure_fails_with_nonexistent_service_identifier(self):
        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                QmaticConfigurationStep,
                yaml_source=QMATIC_CONFIG_STEP_MINIMAL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Unable to retrieve Service with identifier `qmatic-service`. Try "
            "first configuring the `zgw_consumers` configuration steps.",
        )

    def test_configure_fails_with_wrong_api_type(self):
        ServiceFactory(
            slug="qmatic-service", api_root=QMATIC_API_ROOT, api_type=APITypes.zrc
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                QmaticConfigurationStep,
                yaml_source=QMATIC_CONFIG_STEP_MINIMAL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Found service with identifier `qmatic-service`, but expected "
            "`api_type` to equal `orc` and got `zrc`.",
        )

    def test_configure_is_idempotent(self):
        service = ServiceFactory(
            slug="qmatic-service", api_root=QMATIC_API_ROOT, api_type=APITypes.orc
        )

        for _ in range(2):
            execute_single_step(
                QmaticConfigurationStep,
                yaml_source=QMATIC_CONFIG_STEP_FULL_YAML,
            )

        config = QmaticConfig.get_solo()
        self.assertEqual(config.service, service)
        self.assertEqual(config.booking_base_url, "https://qmatic.local/afspraak/")
