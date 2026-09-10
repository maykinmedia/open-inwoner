from pathlib import Path

from django.test import TestCase

from django_setup_configuration.test_utils import execute_single_step

from open_inwoner.configurations.bootstrap.soap import SoapServiceConfigurationStep
from open_inwoner.soap.models import SoapService
from open_inwoner.soap.tests.factories import SoapServiceFactory

BASE_DIR = Path(__file__).parent / "files"
SOAP_SERVICES_CONFIG_STEP_YAML = str(BASE_DIR / "soap_services_config_step.yaml")


class SoapServiceConfigurationStepTest(TestCase):
    def test_configure_creates_service(self):
        execute_single_step(
            SoapServiceConfigurationStep,
            yaml_source=SOAP_SERVICES_CONFIG_STEP_YAML,
        )

        service = SoapService.objects.get(label="ssd-service")
        self.assertEqual(service.url, "http://ssd.internal/")

    def test_configure_updates_existing_service_with_same_identifier(self):
        service = SoapServiceFactory(
            label="ssd-service", url="http://ssd.internal:1234/stale/"
        )

        execute_single_step(
            SoapServiceConfigurationStep,
            yaml_source=SOAP_SERVICES_CONFIG_STEP_YAML,
        )

        service.refresh_from_db()
        self.assertEqual(service.url, "http://ssd.internal/")
        self.assertEqual(SoapService.objects.count(), 1)

    def test_configure_is_idempotent(self):
        for _ in range(2):
            execute_single_step(
                SoapServiceConfigurationStep,
                yaml_source=SOAP_SERVICES_CONFIG_STEP_YAML,
            )

        self.assertEqual(SoapService.objects.count(), 1)
        service = SoapService.objects.get(label="ssd-service")
        self.assertEqual(service.url, "http://ssd.internal/")
