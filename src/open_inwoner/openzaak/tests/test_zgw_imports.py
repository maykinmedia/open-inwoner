from django.test import TestCase

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

        # Move to MockData? No, because we also test without (flag it?)
        cat_configs = {root: dict() for root in self.roots}
        for root in self.roots:
            cat_configs[root]["AAA"] = CatalogusConfigFactory.create(
                url=data[root].zaak_types[0]["catalogus"]
            )
            cat_configs[root]["BBB"] = CatalogusConfigFactory.create(
                url=data[root].zaak_types[1]["catalogus"]
            )

        res = import_zaaktype_configs()

        # Note also that the multi-backend ZGW client is threaded, so we can't rely on the ordering
        # of the responses here and thus compare sets.
        expected_res = set()
        for root in self.roots:
            expected_res.add(
                (
                    data[root].zaak_types[0]["identificatie"],
                    data[root].zaak_types[0]["omschrijving"],
                    # Verify that the correct catalog is used for the identificatie
                    cat_configs[root][data[root].zaak_types[0]["identificatie"]],
                    # zaak 3 has the same identificatie, but different url, which gets merged
                    # into the existing ZaakTypeconfig
                    data[root].zaak_types[0]["url"],
                    data[root].zaak_types[2]["url"],
                )
            )
            expected_res.add(
                (
                    data[root].zaak_types[1]["identificatie"],
                    data[root].zaak_types[1]["omschrijving"],
                    cat_configs[root][data[root].zaak_types[1]["identificatie"]],
                    data[root].zaak_types[1]["url"],
                )
            )

        self.assertEqual(
            {
                (
                    c.identificatie,
                    c.omschrijving,
                    c.catalogus,
                    *c.urls,
                )
                for c in res
            },
            expected_res,
            msg=(
                "First two should be added, third one has same identificatie so its url"
                " should be merged into the first, the fourth one is internal and should"
                " be skipped."
            ),
        )
        self.assertEqual(
            [r.pk for r in res],
            list(ZaakTypeConfig.objects.values_list("pk", flat=True)),
            msg="Only the imported configs should be created",
        )

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

        # Two added: one for each root
        self.assertEqual(len(res), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 6)
        self.assertEqual(
            {
                (
                    c.identificatie,
                    c.omschrijving,
                    c.catalogus,
                    *c.urls,
                )
                for c in res
            },
            {
                (
                    data[root].extra_zaaktype["identificatie"],
                    data[root].extra_zaaktype["omschrijving"],
                    # Verify that the correct catalog is used for the identificatie
                    cat_configs[root][data[root].zaak_types[0]["identificatie"]],
                    data[root].extra_zaaktype["url"],
                )
                for root in self.roots
            },
        )

    def test_import_zaaktype_configs_without_catalogs(self, m):
        for root in self.roots:
            data = ZaakTypeMockData(root)
            data.install_mocks(m)

        with self.assertRaises(
            RuntimeError, msg="Catalogus must exist prior to import"
        ):
            import_zaaktype_configs()
