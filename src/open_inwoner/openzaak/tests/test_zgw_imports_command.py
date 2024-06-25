import inspect
from io import StringIO

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
            CatalogMockData(root).install_mocks(m)
            InformationObjectTypeMockData(root).install_mocks(m)
            # ZaakTypeMockData(root).install_mocks(m)

            # TODO: ADD CATALOGI like in iotypes

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
        aaaaa - 123456789
        aaaaa - 123456789
        bbbbb - 123456789
        bbbbb - 123456789

        imported 4 new zaaktype configs
        AAA - zaaktype-aaa
        AAA - zaaktype-aaa
        BBB - zaaktype-bbb
        BBB - zaaktype-bbb

        imported 6 new zaaktype-informatiebjecttype configs
        AAA - zaaktype-aaa
          info-aaa-1
          info-aaa-2
        AAA - zaaktype-aaa
          info-aaa-1
          info-aaa-2
        BBB - zaaktype-bbb
          info-bbb
        BBB - zaaktype-bbb
          info-bbb

        imported 4 new zaaktype-statustype configs
        AAA - zaaktype-aaa
          AAA - status-aaa-1
          AAA - status-aaa-2
        AAA - zaaktype-aaa
          AAA - status-aaa-1
          AAA - status-aaa-2

        imported 4 new zaaktype-resultaattype configs
        AAA - zaaktype-aaa
          AAA - test
        AAA - zaaktype-aaa
          AAA - test
        BBB - zaaktype-bbb
          BBB - test
        BBB - zaaktype-bbb
          BBB - test
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
