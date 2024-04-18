from io import StringIO
from unittest.mock import patch

from django.core.management import call_command

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


class SetupConfigurationTests(APITestCase):
    maxDiff = None

    @patch(
        "open_inwoner.configurations.bootstrap.zgw.ZakenAPIConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.zgw.CatalogiAPIConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.zgw.DocumentenAPIConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.zgw.FormulierenAPIConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.zgw.ZGWAPIsConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.kic.KlantenAPIConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.kic.ContactmomentenAPIConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.kic.KICAPIsConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.siteconfig.SiteConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.auth.DigiDOIDCConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.auth.eHerkenningOIDCConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.auth.AdminOIDCConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.auth.DigiDConfigurationStep.configure"
    )
    @patch(
        "open_inwoner.configurations.bootstrap.auth.eHerkenningConfigurationStep.configure"
    )
    def test_setup_configuration_success(self, *mocks):
        stdout = StringIO()

        call_command(
            "setup_configuration",
            no_selftest=True,
            stdout=stdout,
            no_color=True,
        )

        steps_to_configure = [
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

        command_output = stdout.getvalue().splitlines()
        expected_output = [
            "Configuration will be set up with following steps: "
            f"[{', '.join(str(step) for step in steps_to_configure)}]",
            f"Configuring {ZakenAPIConfigurationStep()}...",
            f"{ZakenAPIConfigurationStep()} is successfully configured",
            f"Configuring {CatalogiAPIConfigurationStep()}...",
            f"{CatalogiAPIConfigurationStep()} is successfully configured",
            f"Configuring {DocumentenAPIConfigurationStep()}...",
            f"{DocumentenAPIConfigurationStep()} is successfully configured",
            f"Configuring {FormulierenAPIConfigurationStep()}...",
            f"{FormulierenAPIConfigurationStep()} is successfully configured",
            f"Configuring {ZGWAPIsConfigurationStep()}...",
            f"{ZGWAPIsConfigurationStep()} is successfully configured",
            f"Configuring {KlantenAPIConfigurationStep()}...",
            f"{KlantenAPIConfigurationStep()} is successfully configured",
            f"Configuring {ContactmomentenAPIConfigurationStep()}...",
            f"{ContactmomentenAPIConfigurationStep()} is successfully configured",
            f"Configuring {KICAPIsConfigurationStep()}...",
            f"{KICAPIsConfigurationStep()} is successfully configured",
            f"Configuring {SiteConfigurationStep()}...",
            f"{SiteConfigurationStep()} is successfully configured",
            f"Configuring {DigiDOIDCConfigurationStep()}...",
            f"{DigiDOIDCConfigurationStep()} is successfully configured",
            f"Configuring {eHerkenningOIDCConfigurationStep()}...",
            f"{eHerkenningOIDCConfigurationStep()} is successfully configured",
            f"Configuring {AdminOIDCConfigurationStep()}...",
            f"{AdminOIDCConfigurationStep()} is successfully configured",
            f"Configuring {DigiDConfigurationStep()}...",
            f"{DigiDConfigurationStep()} is successfully configured",
            f"Configuring {eHerkenningConfigurationStep()}...",
            f"{eHerkenningConfigurationStep()} is successfully configured",
            "Selftest is skipped.",
            "Instance configuration completed.",
        ]

        self.assertEqual(command_output, expected_output)
