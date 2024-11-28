import inspect
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

import requests_mock

from open_inwoner.openzaak.models import (
    CatalogusConfig,
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.openzaak.tests.shared import ANOTHER_CATALOGI_ROOT, CATALOGI_ROOT
from open_inwoner.openzaak.tests.test_zgw_imports import CatalogMockData
from open_inwoner.openzaak.tests.test_zgw_imports_iotypes import (
    InformationObjectTypeMockData,
)
from open_inwoner.openzaak.zgw_imports import import_catalog_configs
from open_inwoner.utils.test import ClearCachesMixin


@requests_mock.Mocker()
class ZGWImportTest(ClearCachesMixin, TestCase):
    config: OpenZaakConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = OpenZaakConfig.get_solo()
        cls.roots = (CATALOGI_ROOT, ANOTHER_CATALOGI_ROOT)
        cls.api_groups_for_root = {
            root: ZGWApiGroupConfigFactory(ztc_service__api_root=root)
            for root in cls.roots
        }

    def test_zgw_import_data_command(self, m):
        m.reset_mock()
        for root in self.roots:
            InformationObjectTypeMockData(root).install_mocks(m)
            CatalogMockData(root).install_mocks(m)

        # run it to import our data
        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        self.assertEqual(CatalogusConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 6)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 4)

        stdout = out.getvalue().strip()

        expected = inspect.cleandoc(
            """
        imported 4 new catalogus configs
        aaaaa - 123456789 [andere-catalogi.nl]
        aaaaa - 123456789 [catalogi.nl]
        bbbbb - 123456789 [andere-catalogi.nl]
        bbbbb - 123456789 [catalogi.nl]

        imported 4 new zaaktype configs
        AAA - zaaktype-aaa [andere-catalogi.nl]
        AAA - zaaktype-aaa [catalogi.nl]
        BBB - zaaktype-bbb [andere-catalogi.nl]
        BBB - zaaktype-bbb [catalogi.nl]

        imported 6 new zaaktype-informatiebjecttype configs
        AAA - zaaktype-aaa [andere-catalogi.nl]
          info-aaa-1 [andere-catalogi.nl]
          info-aaa-2 [andere-catalogi.nl]
        AAA - zaaktype-aaa [catalogi.nl]
          info-aaa-1 [catalogi.nl]
          info-aaa-2 [catalogi.nl]
        BBB - zaaktype-bbb [andere-catalogi.nl]
          info-bbb [andere-catalogi.nl]
        BBB - zaaktype-bbb [catalogi.nl]
          info-bbb [catalogi.nl]

        imported 4 new zaaktype-statustype configs
        AAA - zaaktype-aaa [andere-catalogi.nl]
          AAA - status-aaa-1 [andere-catalogi.nl]
          AAA - status-aaa-2 [andere-catalogi.nl]
        AAA - zaaktype-aaa [catalogi.nl]
          AAA - status-aaa-1 [catalogi.nl]
          AAA - status-aaa-2 [catalogi.nl]

        imported 4 new zaaktype-resultaattype configs
        AAA - zaaktype-aaa [andere-catalogi.nl]
          AAA - test [andere-catalogi.nl]
        AAA - zaaktype-aaa [catalogi.nl]
          AAA - test [catalogi.nl]
        BBB - zaaktype-bbb [andere-catalogi.nl]
          BBB - test [andere-catalogi.nl]
        BBB - zaaktype-bbb [catalogi.nl]
          BBB - test [catalogi.nl]
        """
        ).strip()

        self.assertEqual(stdout, expected)

        # run it again without changes
        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        # still same
        self.assertEqual(CatalogusConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 6)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 4)
        stdout = out.getvalue().strip()

        expected = inspect.cleandoc(
            """
        imported 0 new catalogus configs

        imported 0 new zaaktype configs

        imported 0 new zaaktype-informatiebjecttype configs

        imported 0 new zaaktype-statustype configs

        imported 0 new zaaktype-resultaattype configs
        """
        ).strip()

        self.assertEqual(stdout, expected)


class ZGWImportCommandWithoutConfigTest(TestCase):
    def test_command_exits_early_if_no_zgw_api_defined(
        self,
    ):
        mock_import_catalog_configs = mock.create_autospec(
            import_catalog_configs, side_effect=import_catalog_configs
        )

        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        self.assertEqual(
            out.getvalue(),
            "Please define at least one ZGWApiGroupConfig before running this command.\n",
        )
        mock_import_catalog_configs.assert_not_called()
