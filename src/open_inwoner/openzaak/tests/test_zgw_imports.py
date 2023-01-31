from io import StringIO

from django.core.management import call_command
from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.openzaak.models import CatalogusConfig, OpenZaakConfig, ZaakTypeConfig
from open_inwoner.openzaak.tests.factories import CatalogusConfigFactory, ServiceFactory
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT
from open_inwoner.openzaak.zgw_imports import (
    import_catalog_configs,
    import_zaaktype_configs,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response


class CatalogMockData:
    def __init__(self):
        self.catalogs = [
            generate_oas_component(
                "ztc",
                "schemas/Catalogus",
                url=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                domein="aaaaa",
                rsin="123456789",
            ),
            generate_oas_component(
                "ztc",
                "schemas/Catalogus",
                url=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                domein="bbbbb",
                rsin="123456789",
            ),
        ]
        self.extra_catalog = generate_oas_component(
            "ztc",
            "schemas/Catalogus",
            url=f"{CATALOGI_ROOT}catalogussen/cccccccc-cccc-cccc-cccc-cccccccccccc",
            domein="ccccc",
            rsin="123456789",
        )

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")

    def install_mocks(self, m) -> "CatalogMockData":
        self.setUpOASMocks(m)
        m.get(
            f"{CATALOGI_ROOT}catalogussen",
            json=paginated_response(self.catalogs),
        )
        return self


class ZaakTypeMockData:
    def __init__(self):
        self.zaak_types = [
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
                catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                identificatie="AAA",
                omschrijving="zaaktype-aaa",
                indicatieInternOfExtern="extern",
            ),
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
                # different catalogus
                catalogus=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                identificatie="BBB",
                omschrijving="zaaktype-bbb",
                indicatieInternOfExtern="extern",
            ),
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
                catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                # re-use identificatie from above
                identificatie="AAA",
                omschrijving="zaaktype-aaa",
                indicatieInternOfExtern="extern",
            ),
            generate_oas_component(
                "ztc",
                "schemas/ZaakType",
                url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
                catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                identificatie="CCC",
                omschrijving="zaaktype-ccc",
                # internal case
                indicatieInternOfExtern="intern",
            ),
        ]
        self.extra_zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="DDD",
            omschrijving="zaaktype-ddd",
            indicatieInternOfExtern="extern",
        )

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")

    def install_mocks(self, m) -> "ZaakTypeMockData":
        self.setUpOASMocks(m)
        m.get(
            f"{CATALOGI_ROOT}zaaktypen",
            json=paginated_response(self.zaak_types),
        )
        return self


@requests_mock.Mocker()
class ZGWImportTest(ClearCachesMixin, TestCase):
    config: OpenZaakConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # services
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.save()

    def test_import_catalogs(self, m):
        data = CatalogMockData().install_mocks(m)

        res = import_catalog_configs()

        # two got added
        self.assertEqual(len(res), 2)
        self.assertEqual(CatalogusConfig.objects.count(), 2)

        for i, config in enumerate(res):
            self.assertEqual(config.url, data.catalogs[i]["url"])
            self.assertEqual(config.domein, data.catalogs[i]["domein"])
            self.assertEqual(config.rsin, data.catalogs[i]["rsin"])

        # run again with same API response
        res = import_catalog_configs()

        # nothing got added
        self.assertEqual(len(res), 0)
        self.assertEqual(CatalogusConfig.objects.count(), 2)

        # add more elements to API response and run again
        m.get(
            f"{CATALOGI_ROOT}catalogussen",
            json=paginated_response([data.extra_catalog] + data.catalogs),
        )
        res = import_catalog_configs()

        # one got added
        self.assertEqual(len(res), 1)
        self.assertEqual(CatalogusConfig.objects.count(), 3)

        config = res[0]
        self.assertEqual(config.url, data.extra_catalog["url"])
        self.assertEqual(config.domein, data.extra_catalog["domein"])
        self.assertEqual(config.rsin, data.extra_catalog["rsin"])

    def test_import_zaaktype_configs_with_catalogs(self, m):
        data = ZaakTypeMockData().install_mocks(m)

        cat_config_aa = CatalogusConfigFactory.create(
            url=data.zaak_types[0]["catalogus"]
        )
        cat_config_bb = CatalogusConfigFactory.create(
            url=data.zaak_types[1]["catalogus"]
        )

        res = import_zaaktype_configs()

        # first two got added, third one has same identificatie, fourth one is internal
        self.assertEqual(len(res), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)

        for i, config in enumerate(res):
            self.assertEqual(config.identificatie, data.zaak_types[i]["identificatie"])
            self.assertEqual(config.omschrijving, data.zaak_types[i]["omschrijving"])
            self.assertEqual(config.catalogus.url, data.zaak_types[i]["catalogus"])

        # check we linked correctly
        self.assertEqual(res[0].catalogus, cat_config_aa)
        self.assertEqual(res[1].catalogus, cat_config_bb)

        # run again with same API response
        res = import_zaaktype_configs()

        # nothing got added
        self.assertEqual(len(res), 0)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)

        # add more elements to API response and run again
        m.get(
            f"{CATALOGI_ROOT}zaaktypen",
            json=paginated_response([data.extra_zaaktype] + data.zaak_types),
        )
        res = import_zaaktype_configs()

        # one got added
        self.assertEqual(len(res), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 3)

        config = res[0]
        self.assertEqual(config.identificatie, data.extra_zaaktype["identificatie"])
        self.assertEqual(config.omschrijving, data.extra_zaaktype["omschrijving"])
        self.assertEqual(config.catalogus.url, data.extra_zaaktype["catalogus"])
        self.assertEqual(config.catalogus, cat_config_aa)

    def test_import_zaaktype_configs_without_catalogs(self, m):
        data = ZaakTypeMockData()
        for zt in data.zaak_types:
            zt["catalogus"] = None
        data.extra_zaaktype["catalogus"] = None
        data.install_mocks(m)

        res = import_zaaktype_configs()

        # first two got added, third one has same identificatie, fourth one is internal
        self.assertEqual(len(res), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)

        for i, config in enumerate(res):
            self.assertEqual(config.identificatie, data.zaak_types[i]["identificatie"])
            self.assertEqual(config.omschrijving, data.zaak_types[i]["omschrijving"])
            self.assertIsNone(config.catalogus)

        # run again with same API response
        res = import_zaaktype_configs()

        # nothing got added
        self.assertEqual(len(res), 0)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)

        # add more elements to API response and run again
        m.get(
            f"{CATALOGI_ROOT}zaaktypen",
            json=paginated_response([data.extra_zaaktype] + data.zaak_types),
        )
        res = import_zaaktype_configs()

        # one got added
        self.assertEqual(len(res), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 3)

        config = res[0]
        self.assertEqual(config.identificatie, data.extra_zaaktype["identificatie"])
        self.assertEqual(config.omschrijving, data.extra_zaaktype["omschrijving"])
        self.assertIsNone(config.catalogus)

    def test_zgw_import_data_command(self, m):
        CatalogMockData().install_mocks(m)
        ZaakTypeMockData().install_mocks(m)

        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        self.assertEqual(CatalogusConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)

        stdout = out.getvalue()
        self.assertIn("imported 2 new catalogi", stdout)
        self.assertIn("aaaaa - 123456789", stdout)
        self.assertIn("bbbbb - 123456789", stdout)
        self.assertIn("imported 2 new zaaktypes", stdout)
        self.assertIn("AAA - zaaktype-aaa", stdout)
        self.assertIn("BBB - zaaktype-bbb", stdout)
