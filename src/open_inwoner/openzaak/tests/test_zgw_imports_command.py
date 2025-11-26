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
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import ANOTHER_CATALOGI_ROOT, CATALOGI_ROOT
from open_inwoner.openzaak.tests.test_zgw_imports import CatalogMockData
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
    maxDiff = None
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
        cls.api_groups = list(cls.api_groups_for_root.values())

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

        # Expected output for initial import with all new items
        expected_lines = [
            "=" * 80,
            f"ZGW Import Results for {self.api_groups[0]}",
            "=" * 80,
            "",
            "📂 Catalogus Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - aaaaa (RSIN: 123456789)",
            "     - bbbbb (RSIN: 123456789)",
            "📋 ZaakType Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - AAA: zaaktype-aaa",
            "     - BBB: zaaktype-bbb",
            "  🔄 Updated (1):",
            "     - AAA: zaaktype-aaa",
            "  ⚠️  Excluded (1):",
            "     - AAA: zaaktype-aaa",
            "       Reason: Object uitgefilterd omdat deze als 'intern' is aangemerkt",
            "📄 InformatieObjectType Configs",
            "-" * 80,
            "  ✨ Created (3):",
            "     - info-aaa-1 (ZaakType: AAA)",
            "     - info-aaa-2 (ZaakType: AAA)",
            "     - info-bbb (ZaakType: BBB)",
            "🔔 StatusType Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - status-aaa-1 (ZaakType: AAA)",
            "     - status-aaa-2 (ZaakType: AAA)",
            "✅ ResultaatType Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - test (ZaakType: AAA)",
            "     - test (ZaakType: BBB)",
            "",
            "=" * 80,
            "Summary",
            "=" * 80,
            "Total Created:  11",
            "Total Updated:  1",
            "Total Excluded: 1",
            "=" * 80,
            "=" * 80,
            f"ZGW Import Results for {self.api_groups[1]}",
            "=" * 80,
            "",
            "📂 Catalogus Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - aaaaa (RSIN: 123456789)",
            "     - bbbbb (RSIN: 123456789)",
            "📋 ZaakType Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - AAA: zaaktype-aaa",
            "     - BBB: zaaktype-bbb",
            "  🔄 Updated (1):",
            "     - AAA: zaaktype-aaa",
            "  ⚠️  Excluded (1):",
            "     - AAA: zaaktype-aaa",
            "       Reason: Object uitgefilterd omdat deze als 'intern' is aangemerkt",
            "📄 InformatieObjectType Configs",
            "-" * 80,
            "  ✨ Created (3):",
            "     - info-aaa-1 (ZaakType: AAA)",
            "     - info-aaa-2 (ZaakType: AAA)",
            "     - info-bbb (ZaakType: BBB)",
            "🔔 StatusType Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - status-aaa-1 (ZaakType: AAA)",
            "     - status-aaa-2 (ZaakType: AAA)",
            "✅ ResultaatType Configs",
            "-" * 80,
            "  ✨ Created (2):",
            "     - test (ZaakType: AAA)",
            "     - test (ZaakType: BBB)",
            "",
            "=" * 80,
            "Summary",
            "=" * 80,
            "Total Created:  11",
            "Total Updated:  1",
            "Total Excluded: 1",
            "=" * 80,
        ]
        expected = "\n".join(expected_lines)
        self.assertEqual(stdout, expected)

        # run it again without changes - the import should detect existing items
        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        # Database counts should remain the same
        self.assertEqual(CatalogusConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 6)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 4)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 4)

        stdout = out.getvalue().strip()

        # On second run, existing items are detected so most sections show "No changes"
        # Only the internal zaaktype exclusion persists since it's filtered each time
        expected_second_run = [
            "=" * 80,
            f"ZGW Import Results for {self.api_groups[0]}",
            "=" * 80,
            "",
            "📂 Catalogus Configs",
            "-" * 80,
            "  No changes",
            "📋 ZaakType Configs",
            "-" * 80,
            "  ⚠️  Excluded (1):",
            "     - AAA: zaaktype-aaa",
            "       Reason: Object uitgefilterd omdat deze als 'intern' is aangemerkt",
            "📄 InformatieObjectType Configs",
            "-" * 80,
            "  No changes",
            "🔔 StatusType Configs",
            "-" * 80,
            "  No changes",
            "✅ ResultaatType Configs",
            "-" * 80,
            "  No changes",
            "",
            "=" * 80,
            "Summary",
            "=" * 80,
            "Total Created:  0",
            "Total Updated:  0",
            "Total Excluded: 1",
            "=" * 80,
            "=" * 80,
            f"ZGW Import Results for {self.api_groups[1]}",
            "=" * 80,
            "",
            "📂 Catalogus Configs",
            "-" * 80,
            "  No changes",
            "📋 ZaakType Configs",
            "-" * 80,
            "  ⚠️  Excluded (1):",
            "     - AAA: zaaktype-aaa",
            "       Reason: Object uitgefilterd omdat deze als 'intern' is aangemerkt",
            "📄 InformatieObjectType Configs",
            "-" * 80,
            "  No changes",
            "🔔 StatusType Configs",
            "-" * 80,
            "  No changes",
            "✅ ResultaatType Configs",
            "-" * 80,
            "  No changes",
            "",
            "=" * 80,
            "Summary",
            "=" * 80,
            "Total Created:  0",
            "Total Updated:  0",
            "Total Excluded: 1",
            "=" * 80,
        ]
        expected_second = "\n".join(expected_second_run)
        self.assertEqual(stdout, expected_second)


class ZGWImportCommandWithoutConfigTest(TestCase):
    @mock.patch(
        "open_inwoner.openzaak.management.commands.zgw_import_data.ZGWCatalogusImporter"
    )
    def test_command_exits_early_if_no_zgw_api_defined(self, mock_importer):
        out = StringIO()
        call_command("zgw_import_data", stdout=out)

        self.assertEqual(
            out.getvalue(),
            "Please define at least one ZGWApiGroupConfig before running this command.\n",
        )
        # Verify the importer was never instantiated
        mock_importer.assert_not_called()
