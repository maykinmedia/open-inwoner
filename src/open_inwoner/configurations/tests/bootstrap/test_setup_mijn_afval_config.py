from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step
from zgw_consumers.constants import APITypes

from open_inwoner.configurations.bootstrap.mijn_afval import (
    MijnAfvalConfigurationStep,
)
from open_inwoner.mijn_afval.models import MijnAfvalConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory

OPENAFVAL_SERVICE_API_ROOT = "http://openafval.internal:8000/api/v1/"

BASE_DIR = Path(__file__).parent / "files"
MIJN_AFVAL_CONFIG_STEP_FULL_YAML = str(BASE_DIR / "mijn_afval_config_step_full.yaml")


class MijnAfvalConfigurationStepTest(TestCase):
    def test_configure(self):
        service = ServiceFactory(
            slug="openafval-service",
            api_root=OPENAFVAL_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )

        execute_single_step(
            MijnAfvalConfigurationStep,
            yaml_source=MIJN_AFVAL_CONFIG_STEP_FULL_YAML,
        )

        config = MijnAfvalConfig.get_solo()
        self.assertEqual(config.openafval_service, service)

    def test_configure_fails_with_nonexistent_service_identifier(self):
        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                MijnAfvalConfigurationStep,
                yaml_source=MIJN_AFVAL_CONFIG_STEP_FULL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Unable to retrieve Service with identifier `openafval-service`. Try "
            "first configuring the `zgw_consumers` configuration steps.",
        )

    def test_configure_fails_with_wrong_service_api_type(self):
        ServiceFactory(
            slug="openafval-service",
            api_root=OPENAFVAL_SERVICE_API_ROOT,
            api_type=APITypes.zrc,
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                MijnAfvalConfigurationStep,
                yaml_source=MIJN_AFVAL_CONFIG_STEP_FULL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Found service with identifier `openafval-service`, but expected "
            "`api_type` to equal `orc` and got `zrc`.",
        )

    def test_configure_is_idempotent(self):
        service = ServiceFactory(
            slug="openafval-service",
            api_root=OPENAFVAL_SERVICE_API_ROOT,
            api_type=APITypes.orc,
        )

        for _ in range(2):
            execute_single_step(
                MijnAfvalConfigurationStep,
                yaml_source=MIJN_AFVAL_CONFIG_STEP_FULL_YAML,
            )

        config = MijnAfvalConfig.get_solo()
        self.assertEqual(config.openafval_service, service)
