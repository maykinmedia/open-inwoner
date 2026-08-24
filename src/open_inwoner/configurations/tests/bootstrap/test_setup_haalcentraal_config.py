from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step
from zgw_consumers.constants import APITypes

from open_inwoner.configurations.bootstrap.haalcentraal import (
    HaalCentraalConfigurationStep,
)
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory

BRP_SERVICE_API_ROOT = "http://hc-brp.internal:5010/haalcentraal/api/brp/"

BASE_DIR = Path(__file__).parent / "files"
HAALCENTRAAL_CONFIG_STEP_FULL_YAML = str(
    BASE_DIR / "haalcentraal_config_step_full.yaml"
)
HAALCENTRAAL_CONFIG_STEP_MINIMAL_YAML = str(
    BASE_DIR / "haalcentraal_config_step_minimal.yaml"
)


class HaalCentraalConfigurationStepTest(TestCase):
    def test_configure_with_full_config(self):
        service = ServiceFactory(
            slug="brp-service",
            api_root=BRP_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )

        execute_single_step(
            HaalCentraalConfigurationStep,
            yaml_source=HAALCENTRAAL_CONFIG_STEP_FULL_YAML,
        )

        config = HaalCentraalConfig.get_solo()
        self.assertEqual(config.service, service)
        self.assertEqual(config.brp_version, "2.3")
        self.assertEqual(
            config.headers,
            [
                {"key": "x-origin-oin", "value": "00000001234567890000"},
                {"key": "x-doelbinding", "value": "BRPACT-Totaal"},
            ],
        )

    def test_configure_with_minimal_config_leaves_omitted_fields_untouched(self):
        service = ServiceFactory(
            slug="brp-service",
            api_root=BRP_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )

        config = HaalCentraalConfig.get_solo()
        config.brp_version = "2.6"
        config.headers = [{"key": "x-existing", "value": "keep-me"}]
        config.save()

        execute_single_step(
            HaalCentraalConfigurationStep,
            yaml_source=HAALCENTRAAL_CONFIG_STEP_MINIMAL_YAML,
        )

        config = HaalCentraalConfig.get_solo()
        self.assertEqual(config.service, service)
        # not present in the minimal YAML, so left as they were
        self.assertEqual(config.brp_version, "2.6")
        self.assertEqual(config.headers, [{"key": "x-existing", "value": "keep-me"}])

    def test_configure_fails_with_nonexistent_service_identifier(self):
        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                HaalCentraalConfigurationStep,
                yaml_source=HAALCENTRAAL_CONFIG_STEP_MINIMAL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Unable to retrieve Service with identifier `brp-service`. Try first "
            "configuring the `zgw_consumers` configuration steps.",
        )

    def test_configure_fails_with_wrong_service_api_type(self):
        ServiceFactory(
            slug="brp-service",
            api_root=BRP_SERVICE_API_ROOT,
            api_type=APITypes.zrc,
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                HaalCentraalConfigurationStep,
                yaml_source=HAALCENTRAAL_CONFIG_STEP_MINIMAL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Found service with identifier `brp-service`, but expected `api_type` "
            "to equal `orc` and got `zrc`.",
        )

    def test_configure_is_idempotent(self):
        service = ServiceFactory(
            slug="brp-service",
            api_root=BRP_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )

        for _ in range(2):
            execute_single_step(
                HaalCentraalConfigurationStep,
                yaml_source=HAALCENTRAAL_CONFIG_STEP_FULL_YAML,
            )

        config = HaalCentraalConfig.get_solo()
        self.assertEqual(config.service, service)
        self.assertEqual(config.brp_version, "2.3")
