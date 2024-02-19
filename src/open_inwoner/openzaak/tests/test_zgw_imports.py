from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.models import CatalogusConfig, OpenZaakConfig, ZaakTypeConfig
from open_inwoner.openzaak.tests.factories import CatalogusConfigFactory, ServiceFactory
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT
from open_inwoner.openzaak.zgw_imports import (
    import_catalog_configs,
    import_zaaktype_configs,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response


class CatalogMockData:
    def __init__(self):
        self.catalogs = [
            generate_oas_component_cached(
                "ztc",
                "schemas/Catalogus",
                url=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                domein="aaaaa",
                rsin="123456789",
            ),
            generate_oas_component_cached(
                "ztc",
                "schemas/Catalogus",
                url=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                domein="bbbbb",
                rsin="123456789",
            ),
        ]
        self.extra_catalog = generate_oas_component_cached(
            "ztc",
            "schemas/Catalogus",
            url=f"{CATALOGI_ROOT}catalogussen/cccccccc-cccc-cccc-cccc-cccccccccccc",
            domein="ccccc",
            rsin="123456789",
        )

    def install_mocks(self, m) -> "CatalogMockData":
        m.get(
            f"{CATALOGI_ROOT}catalogussen",
            json=paginated_response(self.catalogs),
        )
        return self


class ZaakTypeMockData:
    def __init__(self):

        self.zaaktype_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
        )
        self.zaaktype_bbb = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            # different catalogus
            catalogus=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            identificatie="BBB",
            omschrijving="zaaktype-bbb",
            indicatieInternOfExtern="extern",
        )
        self.zaaktype_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # re-use identificatie from above
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
        )
        self.zaaktype_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="CCC",
            omschrijving="zaaktype-ccc",
            # internal case
            indicatieInternOfExtern="intern",
        )
        self.zaak_types = [
            self.zaaktype_aaa_1,
            self.zaaktype_bbb,
            self.zaaktype_aaa_2,
            self.zaaktype_intern,
        ]
        self.extra_zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="DDD",
            omschrijving="zaaktype-ddd",
            indicatieInternOfExtern="extern",
        )
        self.all_zaak_types = [
            self.zaaktype_aaa_1,
            self.zaaktype_bbb,
            self.zaaktype_aaa_2,
            self.zaaktype_intern,
            self.extra_zaaktype,
        ]

    def install_mocks(self, m, *, with_catalog=True) -> "ZaakTypeMockData":
        if not with_catalog:
            for zt in self.all_zaak_types:
                zt["catalogus"] = None

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

        cls.config = OpenZaakConfig.get_solo()
        cls.config.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
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

        # URLs of zaaktype versions should be stored
        self.assertEqual(
            res[0].urls, [data.zaak_types[0]["url"], data.zaak_types[2]["url"]]
        )
        self.assertEqual(res[1].urls, [data.zaak_types[1]["url"]])

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
        data.install_mocks(m, with_catalog=False)

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
