from uuid import UUID

from django.test import TestCase

import requests_mock
from zgw_consumers.constants import APITypes
from zgw_consumers.test import mock_service_oas_get

from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT
from open_inwoner.openzaak.zgw_imports import (
    import_zaaktype_informatieobjecttype_configs,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response


class InformationObjectTypeMockData:
    def __init__(self):

        self.info_type_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijving="info-aaa-1",
        )
        self.info_type_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijving="info-aaa-2",
        )
        self.extra_info_type_aaa_3 = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/aaaaaaaa-aaaa-aaaa-aaaa-333333333333",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            omschrijving="info-aaa-3",
        )

        self.info_type_bbb = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/bbbbbbbb-bbbb-bbbb-bbbb-111111111111",
            # other catalog (matching the zaaktype)
            catalogus=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            omschrijving="info-bbb",
        )

        self.statustype_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # zaaktype=self.zaaktype_aaa_1,
            omschrijving="status-aaa-1",
        )
        self.statustype_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            # zaaktype=self.zaaktype_aaa_2,
            omschrijving="status-aaa-2",
        )

        self.zaaktype_aaa_1 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-111111111111",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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
                f"{CATALOGI_ROOT}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c"
            ],
        )
        self.resultaat_type_1 = generate_oas_component_cached(
            "ztc",
            "schemas/ResultaatType",
            url=f"{CATALOGI_ROOT}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaaktype=self.zaaktype_aaa_1,
            omschrijving="test",
            resultaattypeomschrijving="test1",
            selectielijstklasse="ABC",
        )
        self.zaaktype_bbb = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="bbbbbbbb-bbbb-bbbb-bbbb-111111111111",
            url=f"{CATALOGI_ROOT}zaaktype/bbbbbbbb-bbbb-bbbb-bbbb-111111111111",
            # different catalogus
            catalogus=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            identificatie="BBB",
            omschrijving="zaaktype-bbb",
            indicatieInternOfExtern="extern",
            informatieobjecttypen=[
                self.info_type_bbb["url"],
            ],
            statustypen=[],
            resultaattypen=[
                f"{CATALOGI_ROOT}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c"
            ],
        )
        self.zaaktype_aaa_2 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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
                f"{CATALOGI_ROOT}resultaatypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            ],
        )
        self.zaaktype_aaa_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-444444444444",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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
            url=f"{CATALOGI_ROOT}zaaktype/aaaaaaaa-aaaa-aaaa-aaaa-555555555555",
            catalogus=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")

    def install_mocks(self, m, *, with_catalog=True) -> "InformationObjectTypeMockData":
        self.setUpOASMocks(m)

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
            f"{CATALOGI_ROOT}zaaktypen",
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
            f"{CATALOGI_ROOT}resultaattypen",
            json=paginated_response(
                [
                    self.resultaat_type_1,
                ]
            ),
        )

        if with_catalog:
            cat_a = f"&catalogus={CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            cat_b = f"&catalogus={CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        else:
            cat_a, cat_b = "", ""

            for zt in (
                *self.all_io_types,
                *self.all_zaak_types,
                *self.all_status_types,
            ):
                zt["catalogus"] = None

        m.get(
            f"{CATALOGI_ROOT}zaaktypen?identificatie=AAA{cat_a}",
            json=paginated_response(
                [self.zaaktype_aaa_1, self.zaaktype_aaa_2, self.zaaktype_aaa_intern]
            ),
        )
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?identificatie=BBB{cat_b}",
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
        cls.config.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        cls.config.save()

    def test_import_zaaktype_informatieobjecttype_configs_with_catalog(self, m):
        data = InformationObjectTypeMockData().install_mocks(m)

        catalog_a = CatalogusConfigFactory(
            domein="aaaaa",
            url=f"{CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        catalog_b = CatalogusConfigFactory(
            domein="bbbbb",
            url=f"{CATALOGI_ROOT}catalogussen/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )

        ztc_a = ZaakTypeConfigFactory(
            catalogus=catalog_a,
            identificatie="AAA",
        )
        ztc_b = ZaakTypeConfigFactory(
            catalogus=catalog_b,
            identificatie="BBB",
        )

        res = import_zaaktype_informatieobjecttype_configs()

        self.assertEqual(len(res), 2)
        self.assertEqual(ztc_a.zaaktypeinformatieobjecttypeconfig_set.count(), 2)
        self.assertEqual(ztc_b.zaaktypeinformatieobjecttypeconfig_set.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 3)

        # first ZaakTypeConfig has two ZaakTypes and two InfoObjectTypes
        ztc, ztiotcs = res[0]
        self.assertEqual(ztc.identificatie, data.zaaktype_aaa_1["identificatie"])
        self.assertEqual(len(ztiotcs), 2)

        # one
        self.assertEqual(ztiotcs[0].omschrijving, data.info_type_aaa_1["omschrijving"])
        self.assertEqual(
            ztiotcs[0].informatieobjecttype_url, data.info_type_aaa_1["url"]
        )
        self.assertEqual(
            set(ztiotcs[0].zaaktype_uuids),
            # check both ZaakTypes are referenced
            {UUID(data.zaaktype_aaa_1["uuid"]), UUID(data.zaaktype_aaa_2["uuid"])},
        )

        # two
        self.assertEqual(ztiotcs[1].omschrijving, data.info_type_aaa_2["omschrijving"])
        self.assertEqual(
            ztiotcs[1].informatieobjecttype_url, data.info_type_aaa_2["url"]
        )
        self.assertEqual(
            set(ztiotcs[1].zaaktype_uuids),
            # this InformationObjectType was only used by the second ZaakType
            {UUID(data.zaaktype_aaa_2["uuid"])},
        )

        # other ZaakTypeConfig only one ZaakType and one InfoObjectType
        ztc, ztiotcs = res[1]
        self.assertEqual(ztc.identificatie, data.zaaktype_bbb["identificatie"])
        self.assertEqual(len(ztiotcs), 1)

        self.assertEqual(ztiotcs[0].omschrijving, data.info_type_bbb["omschrijving"])
        self.assertEqual(ztiotcs[0].informatieobjecttype_url, data.info_type_bbb["url"])
        self.assertEqual(
            set(ztiotcs[0].zaaktype_uuids),
            {UUID(data.zaaktype_bbb["uuid"])},
        )

        # run it again with same data
        res = import_zaaktype_informatieobjecttype_configs()

        # no change
        self.assertEqual(len(res), 0)
        self.assertEqual(ztc_a.zaaktypeinformatieobjecttypeconfig_set.count(), 2)
        self.assertEqual(ztc_b.zaaktypeinformatieobjecttypeconfig_set.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 3)

        # run it again with different response
        self.clear_caches()
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?identificatie=AAA&catalogus={CATALOGI_ROOT}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            json=paginated_response(
                [
                    data.zaaktype_aaa_1,
                    data.zaaktype_aaa_2,
                    data.zaaktype_aaa_intern,
                    data.extra_zaaktype_aaa,
                ]
            ),
        )
        res = import_zaaktype_informatieobjecttype_configs()

        # another InfoObjectType got added to ZaakTypeConfig with identificatie AAA
        self.assertEqual(len(res), 1)
        self.assertEqual(ztc_a.zaaktypeinformatieobjecttypeconfig_set.count(), 3)
        self.assertEqual(ztc_b.zaaktypeinformatieobjecttypeconfig_set.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 4)

        ztc, ztiotcs = res[0]
        self.assertEqual(ztc.identificatie, data.extra_zaaktype_aaa["identificatie"])
        self.assertEqual(len(ztiotcs), 1)

        self.assertEqual(
            ztiotcs[0].omschrijving, data.extra_info_type_aaa_3["omschrijving"]
        )
        self.assertEqual(
            ztiotcs[0].informatieobjecttype_url, data.extra_info_type_aaa_3["url"]
        )
        self.assertEqual(
            set(ztiotcs[0].zaaktype_uuids),
            {UUID(data.extra_zaaktype_aaa["uuid"])},
        )

        # check uuids
        ztiotc_aaa_1 = ZaakTypeInformatieObjectTypeConfig.objects.get(
            zaaktype_config=ztc_a, informatieobjecttype_url=data.info_type_aaa_1["url"]
        )
        self.assertEqual(
            set(ztiotc_aaa_1.zaaktype_uuids),
            {
                UUID(data.zaaktype_aaa_1["uuid"]),
                UUID(data.zaaktype_aaa_2["uuid"]),
                UUID(data.extra_zaaktype_aaa["uuid"]),
            },
        )

    def test_import_zaaktype_informatieobjecttype_configs_without_catalog(self, m):
        data = InformationObjectTypeMockData().install_mocks(m, with_catalog=False)

        ztc_a = ZaakTypeConfigFactory(
            identificatie="AAA",
        )
        ztc_b = ZaakTypeConfigFactory(
            identificatie="BBB",
        )

        res = import_zaaktype_informatieobjecttype_configs()

        self.assertEqual(len(res), 2)
        self.assertEqual(ztc_a.zaaktypeinformatieobjecttypeconfig_set.count(), 2)
        self.assertEqual(ztc_b.zaaktypeinformatieobjecttypeconfig_set.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 3)

        # run it again with same data
        res = import_zaaktype_informatieobjecttype_configs()

        self.assertEqual(len(res), 0)
        self.assertEqual(ztc_a.zaaktypeinformatieobjecttypeconfig_set.count(), 2)
        self.assertEqual(ztc_b.zaaktypeinformatieobjecttypeconfig_set.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 3)

        # rest is same as above
