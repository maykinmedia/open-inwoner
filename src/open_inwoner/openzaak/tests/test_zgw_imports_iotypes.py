from uuid import UUID

from django.test import TestCase

import requests_mock

from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    ZaakTypeConfigFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import ANOTHER_CATALOGI_ROOT, CATALOGI_ROOT
from open_inwoner.openzaak.zgw_imports import (
    import_zaaktype_informatieobjecttype_configs,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response


class InformationObjectTypeMockData:
    def __init__(self, root: str):
        self.root = root

        self.info_type_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{self.root}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijving="info-aaa-1",
        )
        self.info_type_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{self.root}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijving="info-aaa-2",
        )
        self.extra_info_type_aaa_3 = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{self.root}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijving="info-aaa-3",
        )

        self.info_type_bbb = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{self.root}informatieobjecttypen/bbbbbbbb-bbbb-bbbb-bbbb-111111111111",
            # other catalog (matching the zaaktype)
            catalogus=f"{self.root}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            omschrijving="info-bbb",
        )

        self.statustype_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{self.root}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # zaaktype=self.zaaktype_aaa_1,
            omschrijving="status-aaa-1",
        )
        self.statustype_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{self.root}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # zaaktype=self.zaaktype_aaa_2,
            omschrijving="status-aaa-2",
        )

        self.zaaktype_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            url=f"{self.root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
            informatieobjecttypen=[
                self.info_type_aaa_1["url"],
            ],
            statustypen=[
                self.statustype_aaa_1["url"],
            ],
            resultaattypen=[
                f"{self.root}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c"
            ],
        )
        self.resultaat_type_1 = generate_oas_component_cached(
            "ztc",
            "schemas/ResultaatType",
            url=f"{self.root}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaaktype=self.zaaktype_aaa_1,
            omschrijving="test",
            resultaattypeomschrijving="test1",
            selectielijstklasse="ABC",
        )
        self.zaaktype_bbb = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="bbbbbbbb-bbbb-bbbb-bbbb-111111111111",
            url=f"{self.root}zaaktype/bbbbbbbb-bbbb-bbbb-bbbb-111111111111",
            # different catalogus
            catalogus=f"{self.root}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            identificatie="BBB",
            omschrijving="zaaktype-bbb",
            indicatieInternOfExtern="extern",
            informatieobjecttypen=[
                self.info_type_bbb["url"],
            ],
            statustypen=[],
            resultaattypen=[
                f"{self.root}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c"
            ],
        )
        self.zaaktype_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            url=f"{self.root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # re-use identificatie from above
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
            informatieobjecttypen=[
                self.info_type_aaa_1["url"],
                self.info_type_aaa_2["url"],
            ],
            statustypen=[
                self.statustype_aaa_2["url"],
            ],
            resultaattypen=[
                f"{self.root}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            ],
        )
        self.zaaktype_aaa_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            url=f"{self.root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # re-use identificatie from above
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            # internal case will be ignored
            indicatieInternOfExtern="intern",
            informatieobjecttypen=[
                self.info_type_aaa_1["url"],
            ],
            statustypen=[],
            resultaattypen=[],
        )
        self.extra_zaaktype_aaa = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            url=f"{self.root}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            catalogus=f"{self.root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # re-use identificatie from above
            identificatie="AAA",
            omschrijving="zaaktype-aaa",
            indicatieInternOfExtern="extern",
            informatieobjecttypen=[
                self.info_type_aaa_1["url"],
                self.info_type_aaa_2["url"],
                # add extra_info_type
                self.extra_info_type_aaa_3["url"],
            ],
            statustypen=[],
            resultaattypen=[
                self.resultaat_type_1["url"],
            ],
        )

        self.all_io_types = [
            self.info_type_aaa_1,
            self.info_type_bbb,
            self.info_type_aaa_2,
            self.extra_info_type_aaa_3,
        ]
        self.all_zaak_types = [
            self.zaaktype_aaa_1,
            self.zaaktype_bbb,
            self.zaaktype_aaa_2,
            self.zaaktype_aaa_intern,
            self.extra_zaaktype_aaa,
        ]
        self.all_status_types = [
            self.statustype_aaa_1,
            self.statustype_aaa_2,
        ]
        self.all_resultaat_types = [
            self.resultaat_type_1,
        ]

    def install_mocks(self, m) -> "InformationObjectTypeMockData":
        for resource in [
            self.info_type_aaa_1,
            self.info_type_bbb,
            self.info_type_aaa_2,
            self.extra_info_type_aaa_3,
            self.statustype_aaa_1,
            self.statustype_aaa_2,
            self.resultaat_type_1,
        ]:
            m.get(resource["url"], json=resource)

        m.get(
            f"{self.root}zaaktypen",
            json=paginated_response(
                [
                    self.zaaktype_aaa_1,
                    self.zaaktype_bbb,
                    self.zaaktype_aaa_2,
                    self.zaaktype_aaa_intern,
                ]
            ),
        )
        m.get(
            f"{self.root}resultaattypen",
            json=paginated_response(
                [
                    self.resultaat_type_1,
                ]
            ),
        )

        cat_a, cat_b = "", ""

        m.get(
            f"{self.root}zaaktypen?identificatie=AAA{cat_a}",
            json=paginated_response(
                [self.zaaktype_aaa_1, self.zaaktype_aaa_2, self.zaaktype_aaa_intern]
            ),
        )
        m.get(
            f"{self.root}zaaktypen?identificatie=BBB{cat_b}",
            json=paginated_response([self.zaaktype_bbb]),
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
        cls.api_groups_for_root = {
            root: ZGWApiGroupConfigFactory(ztc_service__api_root=root)
            for root in cls.roots
        }

    def test_import_zaaktype_informatieobjecttype_configs_with_catalog(self, m):
        data = {
            root: InformationObjectTypeMockData(root).install_mocks(m)
            for root in self.roots
        }

        catalog_and_zaak_type = {}
        for root in self.roots:
            catalog_a = CatalogusConfigFactory(
                domein="aaaaa",
                url=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                service=self.api_groups_for_root[root].ztc_service,
            )
            catalog_b = CatalogusConfigFactory(
                domein="bbbbb",
                url=f"{root}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                service=self.api_groups_for_root[root].ztc_service,
            )

            ztc_a = ZaakTypeConfigFactory(
                catalogus=catalog_a,
                identificatie="AAA",
            )
            ztc_b = ZaakTypeConfigFactory(
                catalogus=catalog_b,
                identificatie="BBB",
            )

            catalog_and_zaak_type[root] = {
                "catalog_a": catalog_a,
                "catalog_b": catalog_b,
                "ztc_a": ztc_a,
                "ztc_b": ztc_b,
            }

        res = import_zaaktype_informatieobjecttype_configs()

        self.assertEqual(len(res), 4)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 6)

        for root in self.roots:
            self.assertEqual(
                catalog_and_zaak_type[root][
                    "ztc_a"
                ].zaaktypeinformatieobjecttypeconfig_set.count(),
                2,
            )
            self.assertEqual(
                catalog_and_zaak_type[root][
                    "ztc_b"
                ].zaaktypeinformatieobjecttypeconfig_set.count(),
                1,
            )

        for root, root_offset in zip(
            self.roots,
            (0, 2),
        ):
            # first ZaakTypeConfig has two ZaakTypes and two InfoObjectTypes
            ztc, ztiotcs = res[root_offset]
            self.assertEqual(
                ztc.identificatie, data[root].zaaktype_aaa_1["identificatie"]
            )
            self.assertEqual(len(ztiotcs), 2)

            # one
            self.assertEqual(
                ztiotcs[0].omschrijving, data[root].info_type_aaa_1["omschrijving"]
            )
            self.assertEqual(
                ztiotcs[0].informatieobjecttype_url,
                data[root].info_type_aaa_1["url"],
            )
            self.assertEqual(
                set(ztiotcs[0].zaaktype_uuids),
                # check both ZaakTypes are referenced
                {
                    UUID(data[root].zaaktype_aaa_1["uuid"]),
                    UUID(data[root].zaaktype_aaa_2["uuid"]),
                },
            )

            # two
            self.assertEqual(
                ztiotcs[1].omschrijving, data[root].info_type_aaa_2["omschrijving"]
            )
            self.assertEqual(
                ztiotcs[1].informatieobjecttype_url, data[root].info_type_aaa_2["url"]
            )
            self.assertEqual(
                set(ztiotcs[1].zaaktype_uuids),
                # this InformationObjectType was only used by the second ZaakType
                {UUID(data[root].zaaktype_aaa_2["uuid"])},
            )

            # other ZaakTypeConfig only one ZaakType and one InfoObjectType
            ztc, ztiotcs = res[root_offset + 1]
            self.assertEqual(
                ztc.identificatie, data[root].zaaktype_bbb["identificatie"]
            )
            self.assertEqual(len(ztiotcs), 1)

            self.assertEqual(
                ztiotcs[0].omschrijving, data[root].info_type_bbb["omschrijving"]
            )
            self.assertEqual(
                ztiotcs[0].informatieobjecttype_url, data[root].info_type_bbb["url"]
            )
            self.assertEqual(
                set(ztiotcs[0].zaaktype_uuids),
                {UUID(data[root].zaaktype_bbb["uuid"])},
            )

        # run it again with same data
        res = import_zaaktype_informatieobjecttype_configs()

        # no change
        self.assertEqual(len(res), 0)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 6)
        for root in self.roots:
            self.assertEqual(
                catalog_and_zaak_type[root][
                    "ztc_a"
                ].zaaktypeinformatieobjecttypeconfig_set.count(),
                2,
            )
            self.assertEqual(
                catalog_and_zaak_type[root][
                    "ztc_b"
                ].zaaktypeinformatieobjecttypeconfig_set.count(),
                1,
            )

        # run it again with different response
        self.clear_caches()

        for root in self.roots:
            m.get(
                f"{root}zaaktypen?identificatie=AAA&catalogus={root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                json=paginated_response(
                    [
                        data[root].zaaktype_aaa_1,
                        data[root].zaaktype_aaa_2,
                        data[root].zaaktype_aaa_intern,
                        data[root].extra_zaaktype_aaa,
                    ]
                ),
            )

        res = import_zaaktype_informatieobjecttype_configs()

        # another InfoObjectType got added to ZaakTypeConfig with identificatie AAA
        self.assertEqual(len(res), 2)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 8)

        for root, root_offset in zip(
            self.roots,
            (0, 1),
        ):
            self.assertEqual(
                catalog_and_zaak_type[root][
                    "ztc_a"
                ].zaaktypeinformatieobjecttypeconfig_set.count(),
                3,
            )
            self.assertEqual(
                catalog_and_zaak_type[root][
                    "ztc_b"
                ].zaaktypeinformatieobjecttypeconfig_set.count(),
                1,
            )
            ztc, ztiotcs = res[root_offset]
            self.assertEqual(
                ztc.identificatie, data[root].extra_zaaktype_aaa["identificatie"]
            )
            self.assertEqual(len(ztiotcs), 1)

            self.assertEqual(
                ztiotcs[0].omschrijving,
                data[root].extra_info_type_aaa_3["omschrijving"],
            )
            self.assertEqual(
                ztiotcs[0].informatieobjecttype_url,
                data[root].extra_info_type_aaa_3["url"],
            )
            self.assertEqual(
                set(ztiotcs[0].zaaktype_uuids),
                {UUID(data[root].extra_zaaktype_aaa["uuid"])},
            )

            # check uuids
            ztiotc_aaa_1 = ZaakTypeInformatieObjectTypeConfig.objects.get(
                zaaktype_config=catalog_and_zaak_type[root]["ztc_a"],
                informatieobjecttype_url=data[root].info_type_aaa_1["url"],
            )
            self.assertEqual(
                set(ztiotc_aaa_1.zaaktype_uuids),
                {
                    UUID(data[root].zaaktype_aaa_1["uuid"]),
                    UUID(data[root].zaaktype_aaa_2["uuid"]),
                    UUID(data[root].extra_zaaktype_aaa["uuid"]),
                },
            )
