import inspect
from io import StringIO
from unittest import skip

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
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT
from open_inwoner.openzaak.tests.test_zgw_imports import CatalogMockData
from open_inwoner.openzaak.tests.test_zgw_imports_iotypes import (
    InformationObjectTypeMockData,
)
from open_inwoner.utils.test import ClearCachesMixin


@requests_mock.Mocker()
class ZGWImportTest(ClearCachesMixin, TestCase):
    config: OpenZaakConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        ZGWApiGroupConfigFactory(
            ztc_service__api_root=CATALOGI_ROOT,
            form_service=None,
        )

    @skip("Being fixed in the next PR")
    def test_zgw_import_data_command(self, m):
        CatalogMockData().install_mocks(m)
        InformationObjectTypeMockData().install_mocks(m)

        # run it to import our data
        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        self.assertEqual(CatalogusConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 3)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 2)

        stdout = out.getvalue().strip()

        expected = inspect.cleandoc(
            """
        imported 2 new catalogus configs
        aaaaa - 123456789
        bbbbb - 123456789

        imported 2 new zaaktype configs
        AAA - zaaktype-aaa
        BBB - zaaktype-bbb

        imported 3 new zaaktype-informatiebjecttype configs
        AAA - zaaktype-aaa
          info-aaa-1
          info-aaa-2
        BBB - zaaktype-bbb
          info-bbb

        imported 2 new zaaktype-statustype configs
        AAA - zaaktype-aaa
          AAA - status-aaa-1
          AAA - status-aaa-2

        imported 2 new zaaktype-resultaattype configs
        AAA - zaaktype-aaa
          AAA - test
        BBB - zaaktype-bbb
          BBB - test
        """
        ).strip()

        self.assertEqual(stdout, expected)

        # run it again without changes
        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        # still same
        self.assertEqual(CatalogusConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 3)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 2)

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

    def test_zgw_import_data_command_without_catalog(self, m):
        m.get(
            f"{CATALOGI_ROOT}catalogussen",
            status_code=500,
        )
        InformationObjectTypeMockData().install_mocks(m, with_catalog=False)

        with self.assertRaises(RuntimeError):
            call_command("zgw_import_data")
