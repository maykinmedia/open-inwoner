from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings

from rest_framework.test import APITestCase

from open_inwoner.configurations.bootstrap.auth import (
    AdminOIDCConfigurationStep,
    DigiDConfigurationStep,
    DigiDOIDCConfigurationStep,
    eHerkenningConfigurationStep,
    eHerkenningOIDCConfigurationStep,
)
from open_inwoner.configurations.bootstrap.kic import (
    ContactmomentenAPIConfigurationStep,
    KICAPIsConfigurationStep,
    KlantenAPIConfigurationStep,
)
from open_inwoner.configurations.bootstrap.siteconfig import SiteConfigurationStep
from open_inwoner.configurations.bootstrap.zgw import (
    CatalogiAPIConfigurationStep,
    DocumentenAPIConfigurationStep,
    FormulierenAPIConfigurationStep,
    ZakenAPIConfigurationStep,
    ZGWAPIsConfigurationStep,
)

STEPS_TO_CONFIGURE = [
    ZakenAPIConfigurationStep(),
    CatalogiAPIConfigurationStep(),
    DocumentenAPIConfigurationStep(),
    FormulierenAPIConfigurationStep(),
    ZGWAPIsConfigurationStep(),
    KlantenAPIConfigurationStep(),
    ContactmomentenAPIConfigurationStep(),
    KICAPIsConfigurationStep(),
    SiteConfigurationStep(),
    DigiDOIDCConfigurationStep(),
    eHerkenningOIDCConfigurationStep(),
    AdminOIDCConfigurationStep(),
    DigiDConfigurationStep(),
    eHerkenningConfigurationStep(),
]

REQUIRED_SETTINGS = {
    setting_name: "SET"
    for step in STEPS_TO_CONFIGURE
    for setting_name in step.required_settings
}


@override_settings(**REQUIRED_SETTINGS)
class SetupConfigurationTests(APITestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.mocks = []
        for step in STEPS_TO_CONFIGURE:
            mock_step = patch(
                f"{step.__class__.__module__}.{step.__class__.__qualname__}.configure"
            )
            self.mocks.append(mock_step)
            mock_step.start()

        def stop_mocks():
            for mock_step in self.mocks:
                mock_step.stop()

        self.addCleanup(stop_mocks)

    def test_setup_configuration_success(self, *mocks):
        stdout = StringIO()

        call_command(
            "setup_configuration",
            no_selftest=True,
            stdout=stdout,
            no_color=True,
        )

        output_per_step = []
        for step in STEPS_TO_CONFIGURE:
            output_per_step.append(f"Configuring {str(step)}...")
            output_per_step.append(f"{str(step)} is successfully configured")

        command_output = stdout.getvalue().splitlines()
        expected_output = [
            "Configuration will be set up with following steps: "
            f"[{', '.join(str(step) for step in STEPS_TO_CONFIGURE)}]",
            *output_per_step,
            "Selftest is skipped.",
            "Instance configuration completed.",
        ]

        self.assertEqual(command_output, expected_output)
