from django.test import TestCase, override_settings

import requests_mock

from open_inwoner.openzaak.models import CatalogusConfig, OpenZaakConfig, ZaakTypeConfig
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import ANOTHER_CATALOGI_ROOT, CATALOGI_ROOT
from open_inwoner.openzaak.zgw_imports import (
    import_catalog_configs,
    import_zaaktype_configs,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response


class CatalogMockData:
    def __init__(self, root: str):
        self.root = root
        self.catalogs = [
            generate_oas_component_cached(
                "ztc",
                "schemas/Catalogus",
                url=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                domein="aaaaa",
                rsin="123456789",
            ),
            generate_oas_component_cached(
                "ztc",
                "schemas/Catalogus",
                url=f"{root}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                domein="bbbbb",
                rsin="123456789",
            ),
        ]
        self.extra_catalog = generate_oas_component_cached(
            "ztc",
            "schemas/Catalogus",
            url=f"{root}catalogussen/cccccccc-cccc-cccc-cccc-cccccccccccc",
            domein="ccccc",
            rsin="123456789",
        )

    def install_mocks(self, m) -> "CatalogMockData":
        m.get(
            f"{self.root}catalogussen",
            json=paginated_response(self.catalogs),
        )
        return self


class ZaakTypeMockData:
    def __init__(self, root: str):
        self.root = root
        self.zaaktype_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            url=f"{root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
        )
        self.zaaktype_bbb = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            url=f"{root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            # different catalogus
            catalogus=f"{root}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            identificatie="BBB",
            omschrijving="zaaktype-bbb",
            indicatieInternOfExtern="extern",
        )
        self.zaaktype_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
            url=f"{root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
            catalogus=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # re-use identificatie from above
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
        )
        self.zaaktype_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            url=f"{root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            catalogus=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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
            url=f"{root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            catalogus=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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

    def install_mocks(self, m) -> "ZaakTypeMockData":
        m.get(
            f"{self.root}zaaktypen",
            json=paginated_response(self.zaak_types),
        )
        return self


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@requests_mock.Mocker()
class ZGWImportTest(ClearCachesMixin, TestCase):
    config: OpenZaakConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.config = OpenZaakConfig.get_solo()
        cls.roots = (CATALOGI_ROOT, ANOTHER_CATALOGI_ROOT)
        for root in cls.roots:
            ZGWApiGroupConfigFactory(ztc_service__api_root=root)

    def test_import_catalogs(self, m):
        data = {root: CatalogMockData(root).install_mocks(m) for root in self.roots}

        res = import_catalog_configs()

        initial_set = set(CatalogusConfig.objects.values_list("url", "domein", "rsin"))
        self.assertEqual(
            initial_set,
            {
                (catalog["url"], catalog["domein"], catalog["rsin"])
                for mock_data in data.values()
                for catalog in mock_data.catalogs
            },
        )

        # run again with same API response
        res = import_catalog_configs()

        # nothing got added
        self.assertEqual(res, [])
        self.assertEqual(
            set(CatalogusConfig.objects.values_list("url", "domein", "rsin")),
            initial_set,
        )

        # add more elements to API response and run again
        for root in self.roots:
            m.get(
                f"{root}catalogussen",
                json=paginated_response(
                    [data[root].extra_catalog] + data[root].catalogs
                ),
            )

        res = import_catalog_configs()

        # Two got added, one for each root
        self.assertEqual(
            {(r.url, r.domein, r.rsin) for r in res},
            set(
                CatalogusConfig.objects.order_by("-pk").values_list(
                    "url", "domein", "rsin"
                )[:2]
            ),
        )

    def test_import_zaaktype_configs_with_catalogs(self, m):
        data = {root: ZaakTypeMockData(root).install_mocks(m) for root in self.roots}

        cat_configs = {root: dict() for root in self.roots}
        for root in self.roots:
            cat_configs[root]["AAA"] = CatalogusConfigFactory.create(
                url=data[root].zaak_types[0]["catalogus"]
            )
            cat_configs[root]["BBB"] = CatalogusConfigFactory.create(
                url=data[root].zaak_types[1]["catalogus"]
            )

        res = import_zaaktype_configs()

        # Per root: first two got added, third one has same identificatie, fourth one is internal
        self.assertEqual(len(res), 4)
        self.assertEqual(ZaakTypeConfig.objects.count(), 4)

        self.assertEqual(
            [
                (config.identificatie, config.omschrijving, config.catalogus.url)
                for config in res
            ],
            [
                (zt["identificatie"], zt["omschrijving"], zt["catalogus"])
                for root in self.roots
                for zt in data[root].zaak_types[:2]
            ],
        )

        # check we linked correctly
        for i, root in zip((0, 2), self.roots):
            self.assertEqual(res[i + 0].catalogus, cat_configs[root]["AAA"])
            self.assertEqual(res[i + 1].catalogus, cat_configs[root]["BBB"])

            # URLs of zaaktype versions should be stored
            self.assertEqual(
                res[i + 0].urls,
                [data[root].zaak_types[0]["url"], data[root].zaak_types[2]["url"]],
            )
            self.assertEqual(res[i + 1].urls, [data[root].zaak_types[1]["url"]])

        # run again with same API response
        res = import_zaaktype_configs()

        # nothing got added
        self.assertEqual(len(res), 0)
        self.assertEqual(ZaakTypeConfig.objects.count(), 4)

        # add more elements to API response and run again
        for root in self.roots:
            m.get(
                f"{root}zaaktypen",
                json=paginated_response(
                    [data[root].extra_zaaktype] + data[root].zaak_types
                ),
            )
        res = import_zaaktype_configs()

        # one got added for each root
        self.assertEqual(len(res), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 6)

        for i, root in enumerate(self.roots):
            config = res[i + 0]
            self.assertEqual(
                config.identificatie, data[root].extra_zaaktype["identificatie"]
            )
            self.assertEqual(
                config.omschrijving, data[root].extra_zaaktype["omschrijving"]
            )
            self.assertEqual(
                config.catalogus.url, data[root].extra_zaaktype["catalogus"]
            )
            self.assertEqual(config.catalogus, cat_configs[root]["AAA"])

    def test_import_zaaktype_configs_without_catalogs(self, m):
        for root in self.roots:
            data = ZaakTypeMockData(root)
            data.install_mocks(m)

        with self.assertRaises(
            RuntimeError, msg="Catalogus must exist prior to import"
        ):
            import_zaaktype_configs()
