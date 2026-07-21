from datetime import date
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase, override_settings

import requests_mock

from open_inwoner.openzaak.models import (
    CatalogusConfig,
    OpenZaakConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)
from open_inwoner.openzaak.tests.factories import (
    CatalogusConfigFactory,
    ServiceFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import ANOTHER_CATALOGI_ROOT, CATALOGI_ROOT
from open_inwoner.openzaak.zgw_imports import (
    ExclusionReason,
    ZGWCatalogusImporter,
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
        cls.api_groups = [
            ZGWApiGroupConfigFactory(ztc_service__api_root=root) for root in cls.roots
        ]

    def test_zgw_catalogus_importer_import_all(self, m):
        """Scaffold test for the new ZGWCatalogusImporter.import_all() method"""
        # Setup mock data for first API group
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        zaaktype_data = ZaakTypeMockData(root).install_mocks(m)

        # Create catalogi so zaaktypen can reference them
        for catalog in catalog_data.catalogs:
            CatalogusConfigFactory.create(url=catalog["url"])

        # Create importer for first API group
        api_group = self.api_groups[0]
        importer = ZGWCatalogusImporter(api_group)

        # Run the full import
        result = importer.import_all()

        self.assertIsNotNone(result)

        # TODO: Add assertions about result structure
        # result should have: catalogi, zaaktypen, informatieobjecttypen, statustypen, resultaattypen
        # Each should have: created, updated, excluded lists

    def test_import_catalogus_configs_create_new(self, m):
        """Test that new catalogus from API is created with all fields"""
        # Setup: mock API with catalog data
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # Verify no catalogi exist yet
        self.assertEqual(CatalogusConfig.objects.count(), 0)

        # Act: import catalogus configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_catalogus_configs()

        # Assert: two catalogi were created
        self.assertEqual(len(result.created), 2)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(CatalogusConfig.objects.count(), 2)

        # Verify all fields are set correctly on created catalogi
        for i, catalog_dict in enumerate(catalog_data.catalogs):
            created_config = result.created[i]

            self.assertEqual(created_config.url, catalog_dict["url"])
            self.assertEqual(created_config.domein, catalog_dict["domein"])
            self.assertEqual(created_config.rsin, catalog_dict["rsin"])
            self.assertEqual(created_config.service, api_group.ztc_service)

    def test_import_catalogus_configs_update_all_fields(self, m):
        """Test that existing catalogus is updated when API fields change"""
        # Setup: create existing catalogus with different values
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # Create a different service to test service update
        other_service = ServiceFactory.create(
            api_root="https://other-catalogi.nl/api/v1/",
            api_type="ztc",
        )

        # Create existing catalogus with values different from the API, to simulate old
        # values
        existing_catalogus = CatalogusConfigFactory.create(
            url=catalog_data.catalogs[0]["url"],
            domein="old-d",
            rsin="00000",
            service=other_service,
        )

        # Act: import catalogus configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_catalogus_configs()

        # Assert: one updated, one created
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(CatalogusConfig.objects.count(), 2)

        # Verify the updated catalogus has all new values from API
        updated_config = result.updated[0]
        self.assertEqual(updated_config.pk, existing_catalogus.pk)
        self.assertEqual(updated_config.url, catalog_data.catalogs[0]["url"])
        self.assertEqual(updated_config.domein, catalog_data.catalogs[0]["domein"])
        self.assertEqual(updated_config.rsin, catalog_data.catalogs[0]["rsin"])
        self.assertEqual(updated_config.service, api_group.ztc_service)

        # Verify database was actually updated
        existing_catalogus.refresh_from_db()
        self.assertEqual(existing_catalogus.domein, catalog_data.catalogs[0]["domein"])
        self.assertEqual(existing_catalogus.rsin, catalog_data.catalogs[0]["rsin"])
        self.assertEqual(existing_catalogus.service, api_group.ztc_service)

    def test_import_catalogus_configs_no_changes_no_save(self, m):
        """Test that existing catalogus matching API data is not saved unnecessarily"""
        # Setup: create existing catalogus with same values as API
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # Create existing catalogus with exact same values as API
        existing_catalogus = CatalogusConfigFactory.create(
            url=catalog_data.catalogs[0]["url"],
            domein=catalog_data.catalogs[0]["domein"],
            rsin=catalog_data.catalogs[0]["rsin"],
            service=api_group.ztc_service,
        )

        # Track the last modified time
        original_save_count = existing_catalogus.pk

        # Act: import catalogus configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_catalogus_configs()

        # Assert: one created (the second catalog), nothing updated
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(CatalogusConfig.objects.count(), 2)

        # Verify the existing catalogus was not in the updated list
        self.assertNotIn(existing_catalogus, result.updated)

        # Verify database record still exists with same values
        existing_catalogus.refresh_from_db()
        self.assertEqual(existing_catalogus.domein, catalog_data.catalogs[0]["domein"])
        self.assertEqual(existing_catalogus.rsin, catalog_data.catalogs[0]["rsin"])
        self.assertEqual(existing_catalogus.service, api_group.ztc_service)

    def test_import_catalogus_configs_api_error(self, m):
        """Test that API errors are tracked in excluded list"""
        # Setup: mock API to raise an exception
        root = self.roots[0]
        api_group = self.api_groups[0]

        # Mock API endpoint to raise an exception
        m.get(
            f"{root}catalogussen",
            exc=ConnectionError("API connection failed"),
        )

        # Verify no catalogi exist yet
        self.assertEqual(CatalogusConfig.objects.count(), 0)

        # Act: import catalogus configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_catalogus_configs()

        # Assert: nothing created, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)
        self.assertEqual(CatalogusConfig.objects.count(), 0)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "Catalogus")
        self.assertEqual(excluded.url, api_group.ztc_service.api_root)
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("API connection failed", excluded.error_message)

    def test_import_catalogus_configs_database_error_on_create(self, m):
        """Test that database errors during create are tracked in excluded list"""
        # Setup: mock API with catalog data
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # Verify no catalogi exist yet
        self.assertEqual(CatalogusConfig.objects.count(), 0)

        # Mock save() to raise an exception for new objects
        with patch.object(CatalogusConfig, "save") as mock_save:
            mock_save.side_effect = Exception("Database constraint violation")

            # Act: import catalogus configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_catalogus_configs()

        # Assert: nothing created, errors tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 2)
        self.assertEqual(CatalogusConfig.objects.count(), 0)

        # Verify the exclusion details for both catalogs
        for i, excluded in enumerate(result.excluded):
            self.assertEqual(excluded.object_type, "Catalogus")
            self.assertEqual(excluded.url, catalog_data.catalogs[i]["url"])
            self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
            self.assertIn("Save failed", excluded.error_message)
            self.assertIn("Database constraint violation", excluded.error_message)

    def test_import_catalogus_configs_database_error_on_update(self, m):
        """Test that database errors during update are tracked in excluded list"""
        # Setup: create existing catalogus with different values
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # Create existing catalogus with old values
        existing_catalogus = CatalogusConfigFactory.create(
            url=catalog_data.catalogs[0]["url"],
            domein="old-d",
            rsin="00000",
            service=ServiceFactory.create(
                api_root="https://other-catalogi.nl/api/v1/",
                api_type="ztc",
            ),
        )

        original_pk = existing_catalogus.pk

        # Mock save() to raise an exception only for existing objects
        original_save = CatalogusConfig.save

        def mock_save_with_error(self, *args, **kwargs):
            # Only raise error for the existing catalogus (has a pk)
            if self.pk == original_pk:
                raise Exception("Database update failed")
            # Allow new objects to be created normally
            return original_save(self, *args, **kwargs)

        with patch.object(CatalogusConfig, "save", mock_save_with_error):
            # Act: import catalogus configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_catalogus_configs()

        # Assert: one created (second catalog), none updated, one excluded
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)
        self.assertEqual(CatalogusConfig.objects.count(), 2)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "Catalogus")
        self.assertEqual(excluded.url, catalog_data.catalogs[0]["url"])
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database update failed", excluded.error_message)

        # Verify the existing catalogus still has old values (update failed)
        existing_catalogus.refresh_from_db()
        self.assertEqual(existing_catalogus.domein, "old-d")
        self.assertEqual(existing_catalogus.rsin, "00000")

    def test_import_zaaktype_configs_create_new(self, m):
        """Test that new zaaktype from API is created with all fields"""
        # Setup: create catalogus and mock API with zaaktype data
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_url = f"{root}zaaktypen/zt-001"
        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        url=zaaktype_url,
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Verify no zaaktypen exist yet
        self.assertEqual(ZaakTypeConfig.objects.count(), 0)

        # Act: import zaaktype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_zaaktype_configs()

        # Assert: one zaaktype was created
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)

        # Verify all fields are set correctly on created zaaktype
        ztc = result.created[0]
        self.assertEqual(ztc.identificatie, "ZAAK-001")
        self.assertEqual(ztc.omschrijving, "Test Zaaktype")
        self.assertEqual(ztc.catalogus, catalogus)
        self.assertEqual(ztc.urls, [zaaktype_url])

    def test_import_zaaktype_configs_update_all_fields(self, m):
        """Test that existing zaaktype is updated when API fields change"""
        # Setup: create existing zaaktype with old values
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        # Create existing zaaktype with old omschrijving and one URL
        existing_ztc = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Old Description",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001-v1"],
        )

        # Mock API returns same zaaktype with updated omschrijving and new URL
        zaaktype_url_v2 = f"{root}zaaktypen/zt-001-v2"
        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        url=zaaktype_url_v2,
                        identificatie="ZAAK-001",
                        omschrijving="Updated Description",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Act: import zaaktype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_zaaktype_configs()

        # Assert: one zaaktype was updated, none created
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)

        # Verify all updatable fields were changed
        existing_ztc.refresh_from_db()
        self.assertEqual(existing_ztc.omschrijving, "Updated Description")
        # URLs should contain both old and new
        self.assertIn(f"{root}zaaktypen/zt-001-v1", existing_ztc.urls)
        self.assertIn(zaaktype_url_v2, existing_ztc.urls)
        self.assertEqual(len(existing_ztc.urls), 2)

    def test_import_zaaktype_configs_preserves_zaken_visible_from(self, m):
        """
        Locally configured visibility must survive a re-import of the zaaktype,
        which the afhandelcomponent updates independently.
        """
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        existing_ztc = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Old Description",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001-v1"],
            zaken_visible_from=date(2026, 5, 1),
        )

        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        url=f"{root}zaaktypen/zt-001-v2",
                        identificatie="ZAAK-001",
                        omschrijving="Updated Description",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_zaaktype_configs()

        self.assertEqual(len(result.updated), 1)
        existing_ztc.refresh_from_db()
        # the API-sourced field is updated, the locally configured one is not
        self.assertEqual(existing_ztc.omschrijving, "Updated Description")
        self.assertEqual(existing_ztc.zaken_visible_from, date(2026, 5, 1))

    def test_import_zaaktype_configs_no_changes_no_save(self, m):
        """Test that when data hasn't changed, no save occurs (optimization)"""
        # Setup: create existing zaaktype with current values
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_url = f"{root}zaaktypen/zt-001"
        existing_ztc = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Current Description",
            catalogus=catalogus,
            urls=[zaaktype_url],
        )

        # Mock API returns same zaaktype with identical values
        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        url=zaaktype_url,
                        identificatie="ZAAK-001",
                        omschrijving="Current Description",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock the save method to track if it's called
        with patch.object(
            ZaakTypeConfig, "save", wraps=ZaakTypeConfig.save
        ) as mock_save:
            # Act: import zaaktype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_zaaktype_configs()

            # Verify save was not called (optimization check)
            mock_save.assert_not_called()

        # Assert: nothing was created or updated
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)

        # Verify values remain unchanged
        existing_ztc.refresh_from_db()
        self.assertEqual(existing_ztc.omschrijving, "Current Description")
        self.assertEqual(existing_ztc.urls, [zaaktype_url])

    def test_import_zaaktype_configs_api_error(self, m):
        """Test that API errors are caught and tracked in excluded list"""
        # Setup
        root = self.roots[0]
        api_group = self.api_groups[0]

        # Mock API endpoint to raise an exception
        m.get(
            f"{root}zaaktypen",
            exc=ConnectionError("API connection failed"),
        )

        # Verify no zaaktypen exist yet
        self.assertEqual(ZaakTypeConfig.objects.count(), 0)

        # Act: import zaaktype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_zaaktype_configs()

        # Assert: nothing created, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 0)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ZaakType")
        self.assertEqual(excluded.url, api_group.ztc_service.api_root)
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("API connection failed", excluded.error_message)

    def test_import_zaaktype_configs_database_error_on_create(self, m):
        """Test that database errors on create are caught and tracked"""
        # Setup: create catalogus and mock API
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_url = f"{root}zaaktypen/zt-001"
        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        url=zaaktype_url,
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock save to raise an exception on create
        original_save = ZaakTypeConfig.save

        def save_with_error(self, *args, **kwargs):
            if self.pk is None:  # Only fail on create
                raise Exception("Database create failed")
            return original_save(self, *args, **kwargs)

        # Verify no zaaktypen exist yet
        self.assertEqual(ZaakTypeConfig.objects.count(), 0)

        with patch.object(ZaakTypeConfig, "save", save_with_error):
            # Act: import zaaktype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_zaaktype_configs()

        # Assert: nothing created, database error tracked
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 0)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ZaakType")
        self.assertEqual(excluded.url, zaaktype_url)
        self.assertEqual(excluded.identificatie, "ZAAK-001")
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Database create failed", excluded.error_message)

    def test_import_zaaktype_configs_database_error_on_update(self, m):
        """Test that database errors on update are caught and tracked"""
        # Setup: create existing zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_url = f"{root}zaaktypen/zt-001"
        existing_ztc = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Old Description",
            catalogus=catalogus,
            urls=[zaaktype_url],
        )

        # Mock API returns zaaktype with updated omschrijving
        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        url=zaaktype_url,
                        identificatie="ZAAK-001",
                        omschrijving="New Description",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock save to raise an exception on update
        original_save = ZaakTypeConfig.save

        def save_with_error(self, *args, **kwargs):
            if self.pk is not None:  # Only fail on update
                raise Exception("Database update failed")
            return original_save(self, *args, **kwargs)

        with patch.object(ZaakTypeConfig, "save", save_with_error):
            # Act: import zaaktype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_zaaktype_configs()

        # Assert: nothing created or updated, database error tracked
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ZaakType")
        self.assertEqual(excluded.url, zaaktype_url)
        self.assertEqual(excluded.identificatie, "ZAAK-001")
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Database update failed", excluded.error_message)

        # Verify the existing zaaktype still has old values (update failed)
        existing_ztc.refresh_from_db()
        self.assertEqual(existing_ztc.omschrijving, "Old Description")

    def test_import_informatieobjecttype_configs_create_new(self, m):
        """Test importing a new informatieobjecttype config for a zaaktype"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with informatieobjecttypen
        # Note: fetch_case_types_by_identification_no_cache queries with identificatie and catalogus params
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        iot_url = f"{root}informatieobjecttypen/iot-001"

        # Mock with query parameters for identificatie and catalogus filtering
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",  # UUID must be in URL
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return informatieobjecttype details
        m.get(
            iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=iot_url,
                omschrijving="Test Document Type",
            ),
        )

        # Act: import informatieobjecttype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_informatieobjecttype_configs_for_zaaktype(
            zaaktype_config
        )

        # Assert: one informatieobjecttype was created
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)

        # Verify the config details
        iot_config = result.created[0]
        self.assertEqual(iot_config.informatieobjecttype_url, iot_url)
        self.assertEqual(iot_config.omschrijving, "Test Document Type")
        self.assertEqual(iot_config.zaaktype_config, zaaktype_config)
        self.assertIn(UUID(zaaktype_uuid), iot_config.zaaktype_uuids)

    def test_import_informatieobjecttype_configs_update_all_fields(self, m):
        """Test updating an existing informatieobjecttype config with all field changes"""
        from open_inwoner.openzaak.models import ZaakTypeInformatieObjectTypeConfig

        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing informatieobjecttype config with old values and no zaaktype_uuids
        iot_url = f"{root}informatieobjecttypen/iot-001"
        existing_config = ZaakTypeInformatieObjectTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            informatieobjecttype_url=iot_url,
            omschrijving="Old Description",
            zaaktype_uuids=[],
        )

        # Mock API to return zaaktype with informatieobjecttypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return informatieobjecttype details with new omschrijving
        m.get(
            iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=iot_url,
                omschrijving="Updated Description",
            ),
        )

        # Act: import informatieobjecttype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_informatieobjecttype_configs_for_zaaktype(
            zaaktype_config
        )

        # Assert: config was updated, not created
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)

        # Verify the config was updated with new values
        existing_config.refresh_from_db()
        self.assertEqual(existing_config.omschrijving, "Updated Description")
        self.assertIn(UUID(zaaktype_uuid), existing_config.zaaktype_uuids)

        # Verify it's the same object that was updated
        self.assertEqual(result.updated[0].id, existing_config.id)

    def test_import_informatieobjecttype_configs_no_changes_no_save(self, m):
        """Test that when no changes are detected, no save occurs and nothing is marked as updated"""

        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing informatieobjecttype config with values that match API
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        iot_url = f"{root}informatieobjecttypen/iot-001"
        existing_config = ZaakTypeInformatieObjectTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            informatieobjecttype_url=iot_url,
            omschrijving="Test Document Type",
            zaaktype_uuids=[UUID(zaaktype_uuid)],
        )

        # Mock API to return zaaktype with informatieobjecttypen
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return informatieobjecttype details with same omschrijving
        m.get(
            iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=iot_url,
                omschrijving="Test Document Type",
            ),
        )

        # Track the save method to verify it's not called
        with patch.object(ZaakTypeInformatieObjectTypeConfig, "save") as mock_save:
            # Act: import informatieobjecttype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_informatieobjecttype_configs_for_zaaktype(
                zaaktype_config
            )

            # Assert: nothing was created, updated, or excluded
            self.assertEqual(len(result.created), 0)
            self.assertEqual(len(result.updated), 0)
            self.assertEqual(len(result.excluded), 0)

            # Verify save was never called since nothing changed
            mock_save.assert_not_called()

    def test_import_informatieobjecttype_configs_api_error(self, m):
        """Test that API errors are handled and informatieobjecttype is excluded"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with informatieobjecttypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        iot_url = f"{root}informatieobjecttypen/iot-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to raise exception for informatieobjecttype (simulating API error)
        m.get(iot_url, exc=ConnectionError("Failed to fetch informatieobjecttype"))

        # Act: import informatieobjecttype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_informatieobjecttype_configs_for_zaaktype(
            zaaktype_config
        )

        # Assert: informatieobjecttype was excluded due to API error
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "InformatieObjectType")
        self.assertEqual(excluded.url, iot_url)
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("Failed to fetch informatieobjecttype", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_informatieobjecttype_configs_zaaktype_fetch_api_error(self, m):
        """Test that an API error when fetching zaaktypes does not raise and is excluded"""
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            exc=ConnectionError("Failed to fetch zaaktypes"),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_informatieobjecttype_configs_for_zaaktype(
            zaaktype_config
        )

        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "InformatieObjectType")
        self.assertEqual(excluded.url, f"{root}zaaktypen/zt-001")
        self.assertEqual(excluded.identificatie, "ZAAK-001")
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("Failed to fetch zaaktypes", excluded.error_message)

    def test_import_informatieobjecttype_configs_database_error_on_create(self, m):
        """Test that database errors during create are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with informatieobjecttypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        iot_url = f"{root}informatieobjecttypen/iot-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return informatieobjecttype details
        m.get(
            iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=iot_url,
                omschrijving="Test Document Type",
            ),
        )

        # Mock save() to raise an exception for new objects
        with patch.object(ZaakTypeInformatieObjectTypeConfig, "save") as mock_save:
            mock_save.side_effect = Exception("Database constraint violation")

            # Act: import informatieobjecttype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_informatieobjecttype_configs_for_zaaktype(
                zaaktype_config
            )

        # Assert: nothing created, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "InformatieObjectType")
        self.assertEqual(excluded.url, iot_url)
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database constraint violation", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_informatieobjecttype_configs_database_error_on_update(self, m):
        """Test that database errors during update are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing informatieobjecttype config
        iot_url = f"{root}informatieobjecttypen/iot-001"
        existing_config = ZaakTypeInformatieObjectTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            informatieobjecttype_url=iot_url,
            omschrijving="Old Description",
            zaaktype_uuids=[],
        )

        # Mock API to return zaaktype with informatieobjecttypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return informatieobjecttype details with updated omschrijving
        m.get(
            iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=iot_url,
                omschrijving="Updated Description",
            ),
        )

        # Mock save() to raise an exception when updating
        original_save = ZaakTypeInformatieObjectTypeConfig.save

        def save_with_error(instance, *args, **kwargs):
            # Only raise error if this is the existing object being updated
            if instance.pk == existing_config.pk:
                raise Exception("Database lock timeout")
            return original_save(instance, *args, **kwargs)

        with patch.object(
            ZaakTypeInformatieObjectTypeConfig,
            "save",
            autospec=True,
            side_effect=save_with_error,
        ):
            # Act: import informatieobjecttype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_informatieobjecttype_configs_for_zaaktype(
                zaaktype_config
            )

        # Assert: nothing created or updated, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "InformatieObjectType")
        self.assertEqual(excluded.url, iot_url)
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database lock timeout", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_informatieobjecttype_configs_copies_config_from_duplicate(self, m):
        """
        When OpenZaak creates a new informatieobjecttype with the same omschrijving,
        OIP config fields are copied from the existing entry to the new one.
        """
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Existing config with configured OIP fields and the old informatieobjecttype URL
        old_iot_url = f"{root}informatieobjecttypen/iot-old"
        ZaakTypeInformatieObjectTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            informatieobjecttype_url=old_iot_url,
            omschrijving="Besluit",
            zaaktype_uuids=[],
            document_upload_enabled=True,
            document_notification_enabled=True,
        )

        # OpenZaak has created a new informatieobjecttype URL for the same omschrijving
        new_iot_url = f"{root}informatieobjecttypen/iot-new"
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[old_iot_url, new_iot_url],
                        statustypen=[],
                        resultaattypen=[],
                    )
                ]
            ),
        )
        m.get(
            old_iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=old_iot_url,
                omschrijving="Besluit",
            ),
        )
        m.get(
            new_iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=new_iot_url,
                omschrijving="Besluit",
            ),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_informatieobjecttype_configs_for_zaaktype(
            zaaktype_config
        )

        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)

        new_config = result.created[0]
        self.assertEqual(new_config.informatieobjecttype_url, new_iot_url)
        self.assertEqual(new_config.omschrijving, "Besluit")
        # OIP config fields copied from the existing entry
        self.assertTrue(new_config.document_upload_enabled)
        self.assertTrue(new_config.document_notification_enabled)

    def test_import_statustype_configs_create_new(self, m):
        """Test importing a new statustype config for a zaaktype"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with statustypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        statustype_url = f"{root}statustypen/st-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return statustype details
        m.get(
            statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=statustype_url,
                omschrijving="Test Status Type",
                statustekst="Test Status Text",
            ),
        )

        # Act: import statustype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        # Assert: one statustype was created
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)

        # Verify the config details
        st_config = result.created[0]
        self.assertEqual(st_config.statustype_url, statustype_url)
        self.assertEqual(st_config.omschrijving, "Test Status Type")
        self.assertEqual(st_config.statustekst, "Test Status Text")
        self.assertEqual(st_config.zaaktype_config, zaaktype_config)
        self.assertIn(UUID(zaaktype_uuid), st_config.zaaktype_uuids)

    def test_import_statustype_configs_update_all_fields(self, m):
        """Test updating an existing statustype config with all field changes"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing statustype config with old values
        statustype_url = f"{root}statustypen/st-001"
        existing_config = ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            statustype_url=statustype_url,
            omschrijving="Old Description",
            statustekst="Old Status Text",
            zaaktype_uuids=[],
        )

        # Mock API to return zaaktype with statustypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return statustype details with new values
        m.get(
            statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=statustype_url,
                omschrijving="Updated Description",
                statustekst="Updated Status Text",
            ),
        )

        # Act: import statustype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        # Assert: config was updated, not created
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)

        # Verify the config was updated with new values
        existing_config.refresh_from_db()
        self.assertEqual(existing_config.omschrijving, "Updated Description")
        self.assertEqual(existing_config.statustekst, "Updated Status Text")
        self.assertIn(UUID(zaaktype_uuid), existing_config.zaaktype_uuids)

        # Verify it's the same object that was updated
        self.assertEqual(result.updated[0].id, existing_config.id)

    def test_import_statustype_configs_no_changes_no_save(self, m):
        """Test that when no changes are detected, no save occurs and nothing is marked as updated"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing statustype config with values that match API
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        statustype_url = f"{root}statustypen/st-001"
        existing_config = ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            statustype_url=statustype_url,
            omschrijving="Test Status Type",
            statustekst="Test Status Text",
            zaaktype_uuids=[UUID(zaaktype_uuid)],
        )

        # Mock API to return zaaktype with statustypen
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return statustype details with same values
        m.get(
            statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=statustype_url,
                omschrijving="Test Status Type",
                statustekst="Test Status Text",
            ),
        )

        # Track the save method to verify it's not called
        with patch.object(ZaakTypeStatusTypeConfig, "save") as mock_save:
            # Act: import statustype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

            # Assert: nothing was created, updated, or excluded
            self.assertEqual(len(result.created), 0)
            self.assertEqual(len(result.updated), 0)
            self.assertEqual(len(result.excluded), 0)

            # Verify save was never called since nothing changed
            mock_save.assert_not_called()

    def test_import_statustype_configs_api_error(self, m):
        """Test that API errors are handled and statustype is excluded"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with statustypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        statustype_url = f"{root}statustypen/st-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to raise exception for statustype (simulating API error)
        m.get(statustype_url, exc=ConnectionError("Failed to fetch statustype"))

        # Act: import statustype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        # Assert: statustype was excluded due to API error
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "StatusType")
        self.assertEqual(excluded.url, statustype_url)
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("Failed to fetch statustype", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_statustype_configs_zaaktype_fetch_api_error(self, m):
        """Test that an API error when fetching zaaktypes does not raise and is excluded"""
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            exc=ConnectionError("Failed to fetch zaaktypes"),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "StatusType")
        self.assertEqual(excluded.url, f"{root}zaaktypen/zt-001")
        self.assertEqual(excluded.identificatie, "ZAAK-001")
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("Failed to fetch zaaktypes", excluded.error_message)

    def test_import_statustype_configs_database_error_on_create(self, m):
        """Test that database errors during create are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with statustypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        statustype_url = f"{root}statustypen/st-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return statustype details
        m.get(
            statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=statustype_url,
                omschrijving="Test Status Type",
                statustekst="Test Status Text",
            ),
        )

        # Mock save() to raise an exception for new objects
        with patch.object(ZaakTypeStatusTypeConfig, "save") as mock_save:
            mock_save.side_effect = Exception("Database constraint violation")

            # Act: import statustype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        # Assert: nothing created, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "StatusType")
        self.assertEqual(excluded.url, statustype_url)
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database constraint violation", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_statustype_configs_database_error_on_update(self, m):
        """Test that database errors during update are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing statustype config
        statustype_url = f"{root}statustypen/st-001"
        existing_config = ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            statustype_url=statustype_url,
            omschrijving="Old Description",
            statustekst="Old Status Text",
            zaaktype_uuids=[],
        )

        # Mock API to return zaaktype with statustypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )

        # Mock API to return statustype details with updated fields
        m.get(
            statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=statustype_url,
                omschrijving="Updated Description",
                statustekst="Updated Status Text",
            ),
        )

        # Mock save() to raise an exception when updating
        original_save = ZaakTypeStatusTypeConfig.save

        def save_with_error(instance, *args, **kwargs):
            # Only raise error if this is the existing object being updated
            if instance.pk == existing_config.pk:
                raise Exception("Database lock timeout")
            return original_save(instance, *args, **kwargs)

        with patch.object(
            ZaakTypeStatusTypeConfig,
            "save",
            autospec=True,
            side_effect=save_with_error,
        ):
            # Act: import statustype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        # Assert: nothing created or updated, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "StatusType")
        self.assertEqual(excluded.url, statustype_url)
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database lock timeout", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_statustype_configs_copies_config_from_duplicate(self, m):
        """
        When OpenZaak creates a new statustype with the same omschrijving,
        OIP config fields are copied from the existing entry to the new one.
        """
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Existing config with configured OIP fields and the old statustype URL
        old_statustype_url = f"{root}statustypen/st-old"
        description_doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Status beschrijving"}],
                }
            ],
        }
        doc_upload_description_doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Upload instructies"}],
                }
            ],
        }
        ZaakTypeStatusTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            statustype_url=old_statustype_url,
            omschrijving="In behandeling",
            statustekst="Uw zaak wordt behandeld",
            zaaktype_uuids=[],
            status_indicator="warning",
            status_indicator_text="Let op",
            notify_status_change=False,
            action_required=True,
            document_upload_enabled=False,
            description=description_doc,
            document_upload_description=doc_upload_description_doc,
            call_to_action_url="https://example.com",
            call_to_action_text="Actie vereist",
            case_link_text="Bekijk zaak",
        )

        # OpenZaak has created a new statustype URL for the same omschrijving
        new_statustype_url = f"{root}statustypen/st-new"
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[old_statustype_url, new_statustype_url],
                        resultaattypen=[],
                    )
                ]
            ),
        )
        m.get(
            old_statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=old_statustype_url,
                omschrijving="In behandeling",
                statustekst="Uw zaak wordt behandeld",
            ),
        )
        m.get(
            new_statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=new_statustype_url,
                omschrijving="In behandeling",
                statustekst="Uw zaak wordt behandeld",
            ),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_statustype_configs_for_zaaktype(zaaktype_config)

        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)

        new_config = result.created[0]
        self.assertEqual(new_config.statustype_url, new_statustype_url)
        self.assertEqual(new_config.omschrijving, "In behandeling")
        # OIP config fields copied from the existing entry
        self.assertEqual(new_config.status_indicator, "warning")
        self.assertEqual(new_config.status_indicator_text, "Let op")
        self.assertFalse(new_config.notify_status_change)
        self.assertTrue(new_config.action_required)
        self.assertFalse(new_config.document_upload_enabled)
        self.assertEqual(new_config.description.raw_data, description_doc)
        self.assertEqual(
            new_config.document_upload_description.raw_data, doc_upload_description_doc
        )
        self.assertEqual(new_config.call_to_action_url, "https://example.com")
        self.assertEqual(new_config.call_to_action_text, "Actie vereist")
        self.assertEqual(new_config.case_link_text, "Bekijk zaak")

    def test_import_resultaattype_configs_create_new(self, m):
        """Test importing a new resultaattype config for a zaaktype"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with resultaattypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        resultaattype_url = f"{root}resultaattypen/rt-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API to return resultaattype details
        m.get(
            resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=resultaattype_url,
                omschrijving="Test Resultaat Type",
            ),
        )

        # Act: import resultaattype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        # Assert: one config created
        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)

        # Verify the created config
        rt_config = result.created[0]
        self.assertEqual(rt_config.zaaktype_config, zaaktype_config)
        self.assertEqual(rt_config.resultaattype_url, resultaattype_url)
        self.assertEqual(rt_config.omschrijving, "Test Resultaat Type")
        self.assertEqual(len(rt_config.zaaktype_uuids), 1)
        self.assertIn(UUID(zaaktype_uuid), rt_config.zaaktype_uuids)

        # Verify it was saved to the database
        self.assertIsNotNone(rt_config.pk)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 1)

    def test_import_resultaattype_configs_update_all_fields(self, m):
        """Test updating an existing resultaattype config with new values"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing resultaattype config with old values
        resultaattype_url = f"{root}resultaattypen/rt-001"
        existing_config = ZaakTypeResultaatTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            resultaattype_url=resultaattype_url,
            omschrijving="Old Description",
            zaaktype_uuids=[],
        )

        # Mock API to return zaaktype with resultaattypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API to return resultaattype details with updated omschrijving
        m.get(
            resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=resultaattype_url,
                omschrijving="Updated Description",
            ),
        )

        # Act: import resultaattype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        # Assert: one config updated
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)

        # Verify the updated config
        rt_config = result.updated[0]
        self.assertEqual(rt_config.pk, existing_config.pk)
        self.assertEqual(rt_config.omschrijving, "Updated Description")
        self.assertEqual(len(rt_config.zaaktype_uuids), 1)
        self.assertIn(UUID(zaaktype_uuid), rt_config.zaaktype_uuids)

        # Verify changes were saved to the database
        rt_config.refresh_from_db()
        self.assertEqual(rt_config.omschrijving, "Updated Description")
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 1)

    def test_import_resultaattype_configs_no_changes_no_save(self, m):
        """Test that no save occurs when data matches existing config"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing resultaattype config with values matching API
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        resultaattype_url = f"{root}resultaattypen/rt-001"
        existing_config = ZaakTypeResultaatTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            resultaattype_url=resultaattype_url,
            omschrijving="Test Resultaat Type",
            zaaktype_uuids=[UUID(zaaktype_uuid)],
        )

        # Mock API to return zaaktype with resultaattypen
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API to return resultaattype details matching existing config
        m.get(
            resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=resultaattype_url,
                omschrijving="Test Resultaat Type",
            ),
        )

        # Act: import resultaattype configs with save mocked
        with patch.object(ZaakTypeResultaatTypeConfig, "save") as mock_save:
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

            # Assert: save was never called since no changes detected
            mock_save.assert_not_called()

        # Assert: nothing created, updated, or excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)

        # Verify config still exists with same values
        rt_config = ZaakTypeResultaatTypeConfig.objects.get(pk=existing_config.pk)
        self.assertEqual(rt_config.omschrijving, "Test Resultaat Type")
        self.assertEqual(rt_config.zaaktype_uuids, [UUID(zaaktype_uuid)])

    def test_import_resultaattype_configs_api_error(self, m):
        """Test that API errors are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with resultaattypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        resultaattype_url = f"{root}resultaattypen/rt-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API to raise connection error when fetching resultaattype
        m.get(resultaattype_url, exc=ConnectionError("Failed to fetch resultaattype"))

        # Act: import resultaattype configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        # Assert: nothing created or updated, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ResultaatType")
        self.assertEqual(excluded.url, resultaattype_url)
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("Failed to fetch resultaattype", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

        # Verify no config was created in database
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 0)

    def test_import_resultaattype_configs_zaaktype_fetch_api_error(self, m):
        """Test that an API error when fetching zaaktypes does not raise and is excluded"""
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            exc=ConnectionError("Failed to fetch zaaktypes"),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ResultaatType")
        self.assertEqual(excluded.url, f"{root}zaaktypen/zt-001")
        self.assertEqual(excluded.identificatie, "ZAAK-001")
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("Failed to fetch zaaktypes", excluded.error_message)

        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 0)

    def test_import_resultaattype_configs_database_error_on_create(self, m):
        """Test that database errors during creation are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Mock API to return zaaktype with resultaattypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        resultaattype_url = f"{root}resultaattypen/rt-001"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API to return resultaattype details
        m.get(
            resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=resultaattype_url,
                omschrijving="Test Resultaat Type",
            ),
        )

        # Mock save() to raise an exception
        with patch.object(ZaakTypeResultaatTypeConfig, "save") as mock_save:
            mock_save.side_effect = Exception("Database constraint violation")

            # Act: import resultaattype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        # Assert: nothing created or updated, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ResultaatType")
        self.assertEqual(excluded.url, resultaattype_url)
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database constraint violation", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_resultaattype_configs_database_error_on_update(self, m):
        """Test that database errors during update are tracked in excluded list"""
        # Setup: create catalogus and zaaktype
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Create existing resultaattype config
        resultaattype_url = f"{root}resultaattypen/rt-001"
        existing_config = ZaakTypeResultaatTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            resultaattype_url=resultaattype_url,
            omschrijving="Old Description",
            zaaktype_uuids=[],
        )

        # Mock API to return zaaktype with resultaattypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API to return resultaattype details with updated omschrijving
        m.get(
            resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=resultaattype_url,
                omschrijving="Updated Description",
            ),
        )

        # Mock save() to raise an exception when updating
        original_save = ZaakTypeResultaatTypeConfig.save

        def save_with_error(instance, *args, **kwargs):
            # Only raise error if this is the existing object being updated
            if instance.pk == existing_config.pk:
                raise Exception("Database lock timeout")
            return original_save(instance, *args, **kwargs)

        with patch.object(
            ZaakTypeResultaatTypeConfig,
            "save",
            autospec=True,
            side_effect=save_with_error,
        ):
            # Act: import resultaattype configs
            importer = ZGWCatalogusImporter(api_group)
            result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        # Assert: nothing created or updated, error tracked in excluded
        self.assertEqual(len(result.created), 0)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 1)

        # Verify the exclusion details
        excluded = result.excluded[0]
        self.assertEqual(excluded.object_type, "ResultaatType")
        self.assertEqual(excluded.url, resultaattype_url)
        self.assertEqual(excluded.reason, ExclusionReason.DATABASE_ERROR)
        self.assertIn("Save failed", excluded.error_message)
        self.assertIn("Database lock timeout", excluded.error_message)
        self.assertEqual(excluded.extra_context["zaaktype_identificatie"], "ZAAK-001")

    def test_import_resultaattype_configs_copies_config_from_duplicate(self, m):
        """
        When OpenZaak creates a new resultaattype with the same omschrijving,
        OIP config fields are copied from the existing entry to the new one.
        """
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )
        zaaktype_config = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Test Zaaktype",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/zt-001"],
        )

        # Existing config with a configured description and the old resultaattype URL
        old_resultaattype_url = f"{root}resultaattypen/rt-old"
        ZaakTypeResultaatTypeConfig.objects.create(
            zaaktype_config=zaaktype_config,
            resultaattype_url=old_resultaattype_url,
            omschrijving="Toegewezen",
            zaaktype_uuids=[],
            description="De zaak is toegewezen aan een behandelaar.",
        )

        # OpenZaak has created a new resultaattype URL for the same omschrijving
        new_resultaattype_url = f"{root}resultaattypen/rt-new"
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"

        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=f"{root}zaaktypen/{zaaktype_uuid}",
                        identificatie="ZAAK-001",
                        omschrijving="Test Zaaktype",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[],
                        statustypen=[],
                        resultaattypen=[old_resultaattype_url, new_resultaattype_url],
                    )
                ]
            ),
        )
        m.get(
            old_resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=old_resultaattype_url,
                omschrijving="Toegewezen",
            ),
        )
        m.get(
            new_resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=new_resultaattype_url,
                omschrijving="Toegewezen",
            ),
        )

        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_resultaattype_configs_for_zaaktype(zaaktype_config)

        self.assertEqual(len(result.created), 1)
        self.assertEqual(len(result.updated), 1)
        self.assertEqual(len(result.excluded), 0)

        new_config = result.created[0]
        self.assertEqual(new_config.resultaattype_url, new_resultaattype_url)
        self.assertEqual(new_config.omschrijving, "Toegewezen")
        # OIP config field copied from the existing entry
        self.assertEqual(
            new_config.description, "De zaak is toegewezen aan een behandelaar."
        )

    def test_full_zaaktype_import_integration(self, m):
        """Integration test: full import with creates, updates, and exclusions"""
        # Setup: create catalogus
        root = self.roots[0]
        api_group = self.api_groups[0]

        catalogus_url = f"{root}catalogussen/1234-5678"
        catalogus = CatalogusConfigFactory.create(
            url=catalogus_url,
            domein="TEST",
            rsin="12345",
            service=api_group.ztc_service,
        )

        # Create existing zaaktype config that will be updated
        existing_zaaktype = ZaakTypeConfig.objects.create(
            identificatie="ZAAK-001",
            omschrijving="Old Description",
            catalogus=catalogus,
            urls=[f"{root}zaaktypen/old-url"],
        )

        # Create existing informatieobjecttype that will be updated
        iot_url = f"{root}informatieobjecttypen/iot-001"
        existing_iot = ZaakTypeInformatieObjectTypeConfig.objects.create(
            zaaktype_config=existing_zaaktype,
            informatieobjecttype_url=iot_url,
            omschrijving="Old IOT Description",
            zaaktype_uuids=[],
        )

        # Mock API: catalog list
        m.get(
            f"{root}catalogussen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/Catalogus",
                        url=catalogus_url,
                        domein="TEST",
                        rsin="12345",
                    )
                ]
            ),
        )

        # Mock API: zaaktype list with two zaaktypen
        zaaktype_uuid = "7092140f-a0fe-4092-a1f8-293d03d2b053"
        zaaktype_url = f"{root}zaaktypen/{zaaktype_uuid}"
        statustype_url = f"{root}statustypen/st-001"
        resultaattype_url = f"{root}resultaattypen/rt-001"
        failing_resultaattype_url = f"{root}resultaattypen/rt-002"

        m.get(
            f"{root}zaaktypen",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=zaaktype_url,
                        identificatie="ZAAK-001",
                        omschrijving="Updated Description",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[statustype_url],
                        resultaattypen=[resultaattype_url, failing_resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API: zaaktype query by identificatie
        m.get(
            f"{root}zaaktypen?identificatie=ZAAK-001",
            json=paginated_response(
                [
                    generate_oas_component_cached(
                        "ztc",
                        "schemas/ZaakType",
                        uuid=zaaktype_uuid,
                        url=zaaktype_url,
                        identificatie="ZAAK-001",
                        omschrijving="Updated Description",
                        catalogus=catalogus_url,
                        indicatieInternOfExtern="extern",
                        informatieobjecttypen=[iot_url],
                        statustypen=[statustype_url],
                        resultaattypen=[resultaattype_url, failing_resultaattype_url],
                    )
                ]
            ),
        )

        # Mock API: informatieobjecttype details (will update existing)
        m.get(
            iot_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/InformatieObjectType",
                url=iot_url,
                omschrijving="Updated IOT Description",
            ),
        )

        # Mock API: statustype details (new)
        m.get(
            statustype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/StatusType",
                url=statustype_url,
                omschrijving="New Status Type",
                statustekst="New Status Text",
            ),
        )

        # Mock API: resultaattype details (new)
        m.get(
            resultaattype_url,
            json=generate_oas_component_cached(
                "ztc",
                "schemas/ResultaatType",
                url=resultaattype_url,
                omschrijving="New Resultaat Type",
            ),
        )

        # Mock API: failing resultaattype (will be excluded)
        m.get(
            failing_resultaattype_url,
            exc=ConnectionError("API unavailable"),
        )

        # Act: perform full import
        importer = ZGWCatalogusImporter(api_group)
        zaaktype_result = importer.import_zaaktype_configs()

        # Verify zaaktype was updated (not created)
        self.assertEqual(len(zaaktype_result.created), 0)
        self.assertEqual(len(zaaktype_result.updated), 1)
        self.assertEqual(len(zaaktype_result.excluded), 0)

        updated_zaaktype = zaaktype_result.updated[0]
        self.assertEqual(updated_zaaktype.pk, existing_zaaktype.pk)
        self.assertEqual(updated_zaaktype.identificatie, "ZAAK-001")
        self.assertEqual(updated_zaaktype.omschrijving, "Updated Description")
        self.assertIn(zaaktype_url, updated_zaaktype.urls)

        # Act: import related configs
        iot_result = importer.import_informatieobjecttype_configs_for_zaaktype(
            updated_zaaktype
        )
        status_result = importer.import_statustype_configs_for_zaaktype(
            updated_zaaktype
        )
        resultaat_result = importer.import_resultaattype_configs_for_zaaktype(
            updated_zaaktype
        )

        # Verify informatieobjecttype was updated
        self.assertEqual(len(iot_result.created), 0)
        self.assertEqual(len(iot_result.updated), 1)
        self.assertEqual(len(iot_result.excluded), 0)
        updated_iot = iot_result.updated[0]
        self.assertEqual(updated_iot.pk, existing_iot.pk)
        self.assertEqual(updated_iot.omschrijving, "Updated IOT Description")
        self.assertIn(UUID(zaaktype_uuid), updated_iot.zaaktype_uuids)

        # Verify statustype was created (new)
        self.assertEqual(len(status_result.created), 1)
        self.assertEqual(len(status_result.updated), 0)
        self.assertEqual(len(status_result.excluded), 0)
        new_status = status_result.created[0]
        self.assertEqual(new_status.statustype_url, statustype_url)
        self.assertEqual(new_status.omschrijving, "New Status Type")
        self.assertEqual(new_status.statustekst, "New Status Text")
        self.assertIn(UUID(zaaktype_uuid), new_status.zaaktype_uuids)

        # Verify resultaattype: one created, one excluded
        self.assertEqual(len(resultaat_result.created), 1)
        self.assertEqual(len(resultaat_result.updated), 0)
        self.assertEqual(len(resultaat_result.excluded), 1)

        new_resultaat = resultaat_result.created[0]
        self.assertEqual(new_resultaat.resultaattype_url, resultaattype_url)
        self.assertEqual(new_resultaat.omschrijving, "New Resultaat Type")
        self.assertIn(UUID(zaaktype_uuid), new_resultaat.zaaktype_uuids)

        excluded = resultaat_result.excluded[0]
        self.assertEqual(excluded.object_type, "ResultaatType")
        self.assertEqual(excluded.url, failing_resultaattype_url)
        self.assertEqual(excluded.reason, ExclusionReason.API_ERROR)
        self.assertIn("API unavailable", excluded.error_message)

        # Verify final database state
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 1)

    def test_import_catalogus_configs_tracks_not_found_in_api(self, m):
        """Test that catalogus configs not found in API are tracked in result.not_found_in_api"""
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # Create an existing catalogus that won't be in the API response
        orphaned_catalogus = CatalogusConfigFactory.create(
            url=f"{root}catalogussen/dddddddd-dddd-dddd-dddd-dddddddddddd",
            domein="ddddd",  # max 5 chars
            rsin="999999999",
            service=api_group.ztc_service,
            found_in_api=True,  # Initially marked as found
        )

        # Act: import catalogus configs
        importer = ZGWCatalogusImporter(api_group)
        result = importer.import_catalogus_configs()

        # Assert: orphaned catalogus is tracked in not_found_in_api
        self.assertEqual(len(result.created), 2)
        self.assertEqual(len(result.updated), 0)
        self.assertEqual(len(result.excluded), 0)
        self.assertEqual(len(result.not_found_in_api), 1)

        # Verify the orphaned catalogus is in the not_found_in_api list
        not_found = result.not_found_in_api[0]
        self.assertEqual(not_found.pk, orphaned_catalogus.pk)
        self.assertEqual(not_found.domein, "ddddd")

        # Verify found_in_api flag was set to False
        orphaned_catalogus.refresh_from_db()
        self.assertFalse(orphaned_catalogus.found_in_api)

    def test_import_zaaktype_configs_tracks_not_found_in_api(self, m):
        """Test that zaaktype configs not found in API are tracked in result.not_found_in_api"""
        root = self.roots[0]
        catalog_data = CatalogMockData(root).install_mocks(m)
        zaaktype_data = ZaakTypeMockData(root).install_mocks(m)
        api_group = self.api_groups[0]

        # First import catalogus
        importer = ZGWCatalogusImporter(api_group)
        importer.import_catalogus_configs()

        # Create an orphaned zaaktype that won't be in the API response
        catalogus = CatalogusConfig.objects.get(
            url=f"{root}catalogussen/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        )
        orphaned_zaaktype = ZaakTypeConfig.objects.create(
            catalogus=catalogus,
            identificatie="ORPHANED",
            omschrijving="Orphaned ZaakType",
            urls=[f"{root}zaaktype/orphaned-orphaned-orphaned-orphaned"],
            found_in_api=True,  # Initially marked as found
        )

        # Act: import zaaktype configs
        result = importer.import_zaaktype_configs()

        # Assert: orphaned zaaktype is tracked in not_found_in_api
        self.assertEqual(len(result.not_found_in_api), 1)

        # Verify the orphaned zaaktype is in the not_found_in_api list
        not_found = result.not_found_in_api[0]
        self.assertEqual(not_found.pk, orphaned_zaaktype.pk)
        self.assertEqual(not_found.identificatie, "ORPHANED")

        # Verify found_in_api flag was set to False
        orphaned_zaaktype.refresh_from_db()
        self.assertFalse(orphaned_zaaktype.found_in_api)

    def test_import_zaaktype_configs_multiple_api_groups_no_false_positives(self, m):
        # Setup: Create two API groups with different catalogs and zaaktypen
        root1 = self.roots[0]
        root2 = self.roots[1]

        catalog_data1 = CatalogMockData(root1).install_mocks(m)
        catalog_data2 = CatalogMockData(root2).install_mocks(m)

        zaaktype_data1 = ZaakTypeMockData(root1).install_mocks(m)
        zaaktype_data2 = ZaakTypeMockData(root2).install_mocks(m)

        api_group1 = self.api_groups[0]
        api_group2 = self.api_groups[1]

        # Import catalogs for both API groups
        importer1 = ZGWCatalogusImporter(api_group1)
        importer2 = ZGWCatalogusImporter(api_group2)

        importer1.import_catalogus_configs()
        importer2.import_catalogus_configs()

        # Import zaaktypen for both API groups
        result1 = importer1.import_zaaktype_configs()
        result2 = importer2.import_zaaktype_configs()

        # Verify both imports created zaaktypen
        self.assertGreater(len(result1.created), 0)
        self.assertGreater(len(result2.created), 0)

        # Verify no false positives: nothing marked as "not found"
        self.assertEqual(len(result1.not_found_in_api), 0)
        self.assertEqual(len(result2.not_found_in_api), 0)

        # Verify all created zaaktypen are marked as found_in_api
        for zt in ZaakTypeConfig.objects.all():
            self.assertTrue(
                zt.found_in_api,
                f"ZaakType {zt.identificatie} from catalogus {zt.catalogus.domein} "
                f"should be marked as found_in_api=True",
            )

        # Now run import for API group 1 again
        result1_reimport = importer1.import_zaaktype_configs()

        # Verify that API group 2's zaaktypen are NOT marked as "not found"
        self.assertEqual(len(result1_reimport.not_found_in_api), 0)

        # Verify API group 2's zaaktypen still have found_in_api=True
        for zt in ZaakTypeConfig.objects.filter(
            catalogus__service=api_group2.ztc_service
        ):
            self.assertTrue(
                zt.found_in_api,
                f"ZaakType {zt.identificatie} from API group 2 should not be affected "
                f"by API group 1's import",
            )
