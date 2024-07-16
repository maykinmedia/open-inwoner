from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings

from rest_framework.test import APITestCase

from open_inwoner.configurations.bootstrap.auth import (
    AdminOIDCConfigurationStep,
    DigiDOIDCConfigurationStep,
    DigiDSAMLConfigurationStep,
    eHerkenningOIDCConfigurationStep,
    eHerkenningSAMLConfigurationStep,
)
from open_inwoner.configurations.bootstrap.cms import (
    CMSBenefitsConfigurationStep,
    CMSCasesConfigurationStep,
    CMSCollaborateConfigurationStep,
    CMSInboxConfigurationStep,
    CMSProductsConfigurationStep,
    CMSProfileConfigurationStep,
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
    CMSBenefitsConfigurationStep(),
    CMSCasesConfigurationStep(),
    CMSCollaborateConfigurationStep(),
    CMSInboxConfigurationStep(),
    CMSProductsConfigurationStep(),
    CMSProfileConfigurationStep(),
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
    AdminOIDCConfigurationStep(),
    DigiDSAMLConfigurationStep(),
    eHerkenningOIDCConfigurationStep(),
    eHerkenningSAMLConfigurationStep(),
]

REQUIRED_SETTINGS = {
    setting_name: "SET"
    for step in STEPS_TO_CONFIGURE
    for setting_name in step.config_settings.required_settings
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
