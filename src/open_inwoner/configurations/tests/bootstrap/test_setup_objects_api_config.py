from pathlib import Path

from django.test import TestCase

from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.test_utils import execute_single_step
from objectsapiclient.models import ObjectsAPIServiceConfiguration
from zgw_consumers.constants import APITypes

from open_inwoner.configurations.bootstrap.objects_api import (
    ObjectsAPIConfigurationStep,
)
from open_inwoner.openzaak.tests.factories import ServiceFactory

OBJECTS_API_ROOT = "http://objects.internal:8000/api/v2/"
OBJECTTYPES_API_ROOT = "http://objecttypes.internal:8000/api/v2/"

BASE_DIR = Path(__file__).parent / "files"
OBJECTS_API_CONFIG_STEP_FULL_YAML = str(BASE_DIR / "objects_api_config_step_full.yaml")


class ObjectsAPIConfigurationStepTest(TestCase):
    def test_configure(self):
        objects_service = ServiceFactory(
            slug="objecten-test", api_root=OBJECTS_API_ROOT, api_type=APITypes.orc
        )
        objecttypes_service = ServiceFactory(
            slug="objecttypen-test",
            api_root=OBJECTTYPES_API_ROOT,
            api_type=APITypes.orc,
        )

        execute_single_step(
            ObjectsAPIConfigurationStep,
            yaml_source=OBJECTS_API_CONFIG_STEP_FULL_YAML,
        )

        config = ObjectsAPIServiceConfiguration.get_solo()
        self.assertEqual(config.objects_api_client_config, objects_service)
        self.assertEqual(config.objecttypes_api_client_config, objecttypes_service)

    def test_configure_fails_with_nonexistent_service_identifier(self):
        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                ObjectsAPIConfigurationStep,
                yaml_source=OBJECTS_API_CONFIG_STEP_FULL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Unable to retrieve Service with identifier `objecten-test`. Try "
            "first configuring the `zgw_consumers` configuration steps.",
        )

    def test_configure_fails_with_wrong_service_api_type(self):
        ServiceFactory(
            slug="objecten-test", api_root=OBJECTS_API_ROOT, api_type=APITypes.zrc
        )
        ServiceFactory(
            slug="objecttypen-test",
            api_root=OBJECTTYPES_API_ROOT,
            api_type=APITypes.orc,
        )

        with self.assertRaises(ConfigurationRunFailed) as exc:
            execute_single_step(
                ObjectsAPIConfigurationStep,
                yaml_source=OBJECTS_API_CONFIG_STEP_FULL_YAML,
            )

        self.assertEqual(
            str(exc.exception),
            "Found service with identifier `objecten-test`, but expected "
            "`api_type` to equal `orc` and got `zrc`.",
        )

    def test_configure_is_idempotent(self):
        objects_service = ServiceFactory(
            slug="objecten-test", api_root=OBJECTS_API_ROOT, api_type=APITypes.orc
        )
        objecttypes_service = ServiceFactory(
            slug="objecttypen-test",
            api_root=OBJECTTYPES_API_ROOT,
            api_type=APITypes.orc,
        )

        for _ in range(2):
            execute_single_step(
                ObjectsAPIConfigurationStep,
                yaml_source=OBJECTS_API_CONFIG_STEP_FULL_YAML,
            )

        config = ObjectsAPIServiceConfiguration.get_solo()
        self.assertEqual(config.objects_api_client_config, objects_service)
        self.assertEqual(config.objecttypes_api_client_config, objecttypes_service)
