import dataclasses
import io
import uuid

from django.core.files.storage.memory import InMemoryStorage
from django.test import TestCase

from open_inwoner.openzaak.import_export import ZGWConfigExport, ZGWConfigImport
from open_inwoner.openzaak.models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)

from ..import_export import ZGWImportError
from .factories import (
    CatalogusConfigFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
    ZaakTypeResultaatTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)


class ZGWExportImportMockData:
    def __init__(self, count=0, with_dupes=False):
        self.original_url = f"https://foo.{count}.maykinmedia.nl"
        self.original_uuid = "a1591906-3368-470a-a957-4b8634c275a1"
        self.service = ServiceFactory(slug=f"service-{count}")
        self.catalogus = CatalogusConfigFactory(
            url=self.original_url,
            domein=f"DM-{count}",
            rsin="123456789",
            service=self.service,
        )
        self.ztc = ZaakTypeConfigFactory(
            catalogus=self.catalogus,
            identificatie=f"ztc-id-a-{count}",
            omschrijving="zaaktypeconfig",
            notify_status_changes=False,
            external_document_upload_url="",
            document_upload_enabled=False,
            contact_form_enabled=False,
            contact_subject_code="",
            relevante_zaakperiode=None,
            urls=[self.original_url],
        )
        self.ztc_status = ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=self.ztc,
            statustype_url=self.original_url,
            omschrijving="status omschrijving",
            statustekst="",
            zaaktype_uuids=[self.original_uuid],
            status_indicator="",
            status_indicator_text="",
            document_upload_description="",
            description="status",
            notify_status_change=True,
            action_required=False,
            document_upload_enabled=True,
            call_to_action_url="",
            call_to_action_text="",
            case_link_text="",
        )
        self.ztc_resultaat = ZaakTypeResultaatTypeConfigFactory(
            zaaktype_config=self.ztc,
            resultaattype_url=self.original_url,
            omschrijving="resultaat",
            zaaktype_uuids=[self.original_uuid],
            description="",
        )
        self.ztiotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=self.ztc,
            informatieobjecttype_url=self.original_url,
            omschrijving="informatieobject",
            zaaktype_uuids=[self.original_uuid],
        )
        if with_dupes:
            self.ztc_resultaat_2 = ZaakTypeResultaatTypeConfigFactory(
                zaaktype_config=self.ztc,
                resultaattype_url=self.original_url,
                omschrijving="status omschrijving",  # test dupes across models
                zaaktype_uuids=[self.original_uuid],
                description="",
            )


class ExportObjectTests(TestCase):
    def setUp(self):
        self.mocks = [
            ZGWExportImportMockData(0),
            ZGWExportImportMockData(1),
        ]

    def test_export_only_accepts_queryset(self):
        for arg in (list(), set(), tuple(), None, "", CatalogusConfig.objects.first()):
            with self.subTest(f"Default factory should not accept {arg}"):
                with self.assertRaises(TypeError):
                    ZGWConfigExport.from_catalogus_configs(arg)

    def test_export_only_accepts_queryset_of_correct_type(self):
        with self.assertRaises(ValueError):
            ZGWConfigExport.from_catalogus_configs(ZaakTypeConfig.objects.all())

    def test_equality_operator(self):
        export_a = ZGWConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[0].catalogus.pk)
        )
        export_b = ZGWConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[1].catalogus.pk)
        )

        self.assertTrue(export_a == export_a)
        self.assertTrue(export_b == export_b)
        self.assertFalse(export_a == export_b)

    def test_only_models_related_to_exported_catalogus_config_are_included(self):
        export = ZGWConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[0].catalogus.pk)
        )

        for export_field, mock_field in zip(
            (
                "catalogus_configs",
                "zaaktype_configs",
                "zaak_status_type_configs",
                "zaak_resultaat_type_configs",
                "zaak_informatie_object_type_configs",
            ),
            (
                "catalogus",
                "ztc",
                "ztc_status",
                "ztc_resultaat",
                "ztiotc",
            ),
        ):
            with self.subTest(
                f"{mock_field} should not be in the export's {export_field} field"
            ):
                self.assertIn(
                    getattr(self.mocks[0], mock_field).pk,
                    getattr(export, export_field).values_list("pk", flat=True),
                    msg="Export should include all instances from the export set",
                )
                self.assertNotIn(
                    getattr(self.mocks[1], mock_field).pk,
                    getattr(export, export_field).values_list("pk", flat=True),
                    msg="Export should not include any instances from the non-exported set",
                )


class ZaakTypeConfigExportTest(TestCase):
    def setUp(self):
        self.mocks = ZGWExportImportMockData(0)

    def test_export_zaaktype_configs(self):
        export = ZGWConfigExport.from_zaaktype_configs(
            ZaakTypeConfig.objects.filter(pk=self.mocks.ztc.pk)
        )
        rows = export.as_dicts()

        expected = [
            {
                "model": "openzaak.zaaktypeconfig",
                "fields": {
                    "urls": '["https://foo.0.maykinmedia.nl"]',
                    "catalogus": ["DM-0", "123456789"],
                    "identificatie": "ztc-id-a-0",
                    "omschrijving": "zaaktypeconfig",
                    "notify_status_changes": False,
                    "description": "",
                    "external_document_upload_url": "",
                    "document_upload_enabled": False,
                    "contact_form_enabled": False,
                    "contact_subject_code": "",
                    "relevante_zaakperiode": None,
                },
            },
            {
                "model": "openzaak.zaaktypeinformatieobjecttypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"],
                    "informatieobjecttype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "informatieobject",
                    "zaaktype_uuids": '["a1591906-3368-470a-a957-4b8634c275a1"]',
                    "document_upload_enabled": False,
                    "document_notification_enabled": False,
                },
            },
            {
                "model": "openzaak.zaaktypestatustypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"],
                    "statustype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "status omschrijving",
                    "statustekst": "",
                    "zaaktype_uuids": '["a1591906-3368-470a-a957-4b8634c275a1"]',
                    "status_indicator": "",
                    "status_indicator_text": "",
                    "document_upload_description": "",
                    "description": "status",
                    "notify_status_change": True,
                    "action_required": False,
                    "document_upload_enabled": True,
                    "call_to_action_url": "",
                    "call_to_action_text": "",
                    "case_link_text": "",
                },
            },
            {
                "model": "openzaak.zaaktyperesultaattypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"],
                    "resultaattype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "resultaat",
                    "zaaktype_uuids": '["a1591906-3368-470a-a957-4b8634c275a1"]',
                    "description": "",
                },
            },
        ]

        self.assertEqual(rows, expected)


class TestCatalogusExport(TestCase):
    def setUp(self):
        self.mocks = [
            ZGWExportImportMockData(0),
            ZGWExportImportMockData(1),
        ]

    def test_export_catalogus_configs(self):
        export = ZGWConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[0].catalogus.pk)
        )
        rows = export.as_dicts()

        expected = [
            {
                "model": "openzaak.catalogusconfig",
                "fields": {
                    "url": "https://foo.0.maykinmedia.nl",
                    "domein": "DM-0",
                    "rsin": "123456789",
                    "service": ["service-0"],
                },
            },
            {
                "model": "openzaak.zaaktypeconfig",
                "fields": {
                    "urls": '["https://foo.0.maykinmedia.nl"]',
                    "catalogus": ["DM-0", "123456789"],
                    "identificatie": "ztc-id-a-0",
                    "omschrijving": "zaaktypeconfig",
                    "notify_status_changes": False,
                    "description": "",
                    "external_document_upload_url": "",
                    "document_upload_enabled": False,
                    "contact_form_enabled": False,
                    "contact_subject_code": "",
                    "relevante_zaakperiode": None,
                },
            },
            {
                "model": "openzaak.zaaktypeinformatieobjecttypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"],
                    "informatieobjecttype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "informatieobject",
                    "zaaktype_uuids": '["a1591906-3368-470a-a957-4b8634c275a1"]',
                    "document_upload_enabled": False,
                    "document_notification_enabled": False,
                },
            },
            {
                "model": "openzaak.zaaktypestatustypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"],
                    "statustype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "status omschrijving",
                    "statustekst": "",
                    "zaaktype_uuids": '["a1591906-3368-470a-a957-4b8634c275a1"]',
                    "status_indicator": "",
                    "status_indicator_text": "",
                    "document_upload_description": "",
                    "description": "status",
                    "notify_status_change": True,
                    "action_required": False,
                    "document_upload_enabled": True,
                    "call_to_action_url": "",
                    "call_to_action_text": "",
                    "case_link_text": "",
                },
            },
            {
                "model": "openzaak.zaaktyperesultaattypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"],
                    "resultaattype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "resultaat",
                    "zaaktype_uuids": '["a1591906-3368-470a-a957-4b8634c275a1"]',
                    "description": "",
                },
            },
        ]

        self.assertEqual(rows, expected)

    def test_export_catalogus_configs_as_jsonl(self):
        export = ZGWConfigExport.from_catalogus_configs(CatalogusConfig.objects.all())
        rows = list(export.as_jsonl_iter())

        expected = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
            "\n",
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.1.maykinmedia.nl", "domein": "DM-1", "rsin": "123456789", "service": ["service-1"]}}',
            "\n",
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.0.maykinmedia.nl\\"]", "catalogus": ["DM-0", "123456789"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            "\n",
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.1.maykinmedia.nl\\"]", "catalogus": ["DM-1", "123456789"], "identificatie": "ztc-id-a-1", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            "\n",
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "informatieobjecttype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[\\"a1591906-3368-470a-a957-4b8634c275a1\\"]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            "\n",
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "DM-1", "123456789"], "informatieobjecttype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[\\"a1591906-3368-470a-a957-4b8634c275a1\\"]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            "\n",
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "statustype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[\\"a1591906-3368-470a-a957-4b8634c275a1\\"]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            "\n",
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "DM-1", "123456789"], "statustype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[\\"a1591906-3368-470a-a957-4b8634c275a1\\"]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            "\n",
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "resultaattype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[\\"a1591906-3368-470a-a957-4b8634c275a1\\"]", "description": ""}}',
            "\n",
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "DM-1", "123456789"], "resultaattype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[\\"a1591906-3368-470a-a957-4b8634c275a1\\"]", "description": ""}}',
            "\n",
        ]

        self.assertEqual(rows, expected)


class TestCatalogusImport(TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.json_lines = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://bar.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://bar.maykinmedia.nl\\"]", "catalogus": ["DM-0", "123456789"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": true, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "informatieobjecttype_url": "https://bar.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[]", "document_upload_enabled": true, "document_notification_enabled": true}}',
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "statustype_url": "https://bar.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "statustekst nieuw", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "resultaattype_url": "https://bar.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[]", "description": "description new"}}',
        ]
        self.json_dupes = [
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "statustype_url": "https://bar.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "statustekst nieuw", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "resultaattype_url": "https://bar.maykinmedia.nl", "omschrijving": "status omschrijving", "zaaktype_uuids": "[]", "description": "description new"}}',
        ]
        self.jsonl = "\n".join(self.json_lines)
        self.jsonl_with_dupes = "\n".join(self.json_lines + self.json_dupes)

    def test_import_jsonl_update_success(self):
        mocks = ZGWExportImportMockData()
        self.storage.save("import.jsonl", io.StringIO(self.jsonl))

        import_result = ZGWConfigImport.import_from_jsonl_file_in_django_storage(
            "import.jsonl", self.storage
        )

        # check import
        self.assertEqual(
            import_result,
            ZGWConfigImport(
                total_rows_processed=5,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_informatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                zaak_resultaat_type_configs_imported=1,
                import_errors=[],
            ),
        )

        # check number of configs
        self.assertEqual(CatalogusConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 1)

        catalogus_config = CatalogusConfig.objects.get()
        zt_config = ZaakTypeConfig.objects.get()
        zt_informatie_objecttype_config = (
            ZaakTypeInformatieObjectTypeConfig.objects.get()
        )
        zt_statustype_config = ZaakTypeStatusTypeConfig.objects.get()
        zt_resultaattype_config = ZaakTypeResultaatTypeConfig.objects.get()

        # check that urls are not overridden
        self.assertEqual(catalogus_config.url, mocks.original_url)
        self.assertEqual(zt_config.urls, [mocks.original_url])
        self.assertEqual(
            zt_informatie_objecttype_config.informatieobjecttype_url,
            mocks.original_url,
        )
        self.assertEqual(zt_statustype_config.statustype_url, mocks.original_url)
        self.assertEqual(zt_resultaattype_config.resultaattype_url, mocks.original_url)

        # check that zaaktype uuids are not overridden
        self.assertEqual(
            zt_informatie_objecttype_config.zaaktype_uuids,
            [uuid.UUID(mocks.original_uuid)],
        )
        self.assertEqual(
            zt_statustype_config.zaaktype_uuids, [uuid.UUID(mocks.original_uuid)]
        )
        self.assertEqual(
            zt_resultaattype_config.zaaktype_uuids, [uuid.UUID(mocks.original_uuid)]
        )

        # check updated content
        zaaktype_statustype_config = ZaakTypeStatusTypeConfig.objects.get()
        self.assertEqual(zaaktype_statustype_config.statustekst, "statustekst nieuw")
        self.assertEqual(zaaktype_statustype_config.notify_status_change, True)

        zaaktype_resultaattype_config = ZaakTypeResultaatTypeConfig.objects.get()
        self.assertEqual(zaaktype_resultaattype_config.description, "description new")

        zaaktype_informatie_objecttype_config = (
            ZaakTypeInformatieObjectTypeConfig.objects.get()
        )
        self.assertEqual(
            zaaktype_informatie_objecttype_config.document_upload_enabled, True
        )
        self.assertEqual(
            zaaktype_informatie_objecttype_config.document_notification_enabled, True
        )

    def test_import_jsonl_missing_statustype_config(self):
        ZGWExportImportMockData()

        # missing ZaakTypeStatusTypeConfig
        json_line_extra = [
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "statustype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "bogus", "statustekst": "bogus", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
        ]
        json_lines = "\n".join(self.json_lines + json_line_extra)

        self.storage.save("import.jsonl", io.StringIO(json_lines))

        # we use `asdict` and replace the Exceptions with string representations
        # because for Exceptions raised from within dataclasses, equality ==/is identity
        import_result = dataclasses.asdict(
            ZGWConfigImport.import_from_jsonl_file_in_django_storage(
                "import.jsonl", self.storage
            )
        )
        expected_error = ZGWImportError(
            "ZaakTypeStatusTypeConfig not found in target environment: omschrijving = 'bogus', "
            "ZaakTypeConfig identificatie = 'ztc-id-a-0'"
        )
        import_expected = dataclasses.asdict(
            ZGWConfigImport(
                total_rows_processed=6,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_informatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                zaak_resultaat_type_configs_imported=1,
                import_errors=[expected_error],
            ),
        )
        import_result["import_errors"][0] = str(import_result["import_errors"][0])
        import_expected["import_errors"][0] = str(import_expected["import_errors"][0])

        # check import
        self.assertEqual(import_result, import_expected)

        # check number of configs
        self.assertEqual(CatalogusConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 1)

    def test_import_jsonl_update_statustype_config_missing_zt_config(self):
        ZGWExportImportMockData()

        # import fails due to missing ZaakTypeConfig
        json_line_extra = [
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["bogus", "DM-1", "666666666"], "statustype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
        ]
        json_lines = "\n".join(self.json_lines + json_line_extra)

        self.storage.save("import.jsonl", io.StringIO(json_lines))

        # we use `asdict` and replace the Exceptions with string representations
        # because for Exceptions raised from within dataclasses, equality ==/is identity
        import_result = dataclasses.asdict(
            ZGWConfigImport.import_from_jsonl_file_in_django_storage(
                "import.jsonl", self.storage
            )
        )
        expected_error = ZGWImportError(
            "ZaakTypeStatusTypeConfig not found in target environment: omschrijving = 'status omschrijving', "
            "ZaakTypeConfig identificatie = 'bogus'"
        )
        import_expected = dataclasses.asdict(
            ZGWConfigImport(
                total_rows_processed=6,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_informatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                zaak_resultaat_type_configs_imported=1,
                import_errors=[expected_error],
            ),
        )
        import_result["import_errors"][0] = str(import_result["import_errors"][0])
        import_expected["import_errors"][0] = str(import_expected["import_errors"][0])

        # check import
        self.assertEqual(import_result, import_expected)

        # check number of configs
        self.assertEqual(CatalogusConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 1)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 1)

    def test_import_jsonl_update_reports_duplicate_db_records(self):
        mocks = ZGWExportImportMockData()

        ZaakTypeResultaatTypeConfigFactory(
            resultaattype_url=mocks.ztc_resultaat.resultaattype_url,
            zaaktype_config=mocks.ztc_resultaat.zaaktype_config,
            omschrijving=mocks.ztc_resultaat.omschrijving,
            description=mocks.ztc_resultaat.description,
        )
        self.storage.save("import.jsonl", io.StringIO(self.jsonl))

        # we use `asdict` and replace the Exceptions with string representations
        # because for Exceptions raised from within dataclasses, equality ==/is identity
        import_result = dataclasses.asdict(
            ZGWConfigImport.import_from_jsonl_file_in_django_storage(
                "import.jsonl", self.storage
            )
        )
        expected_error = ZGWImportError(
            "Got multiple results for ZaakTypeResultaatTypeConfig: omschrijving = 'resultaat', "
            "ZaakTypeConfig identificatie = 'ztc-id-a-0'"
        )
        import_expected = dataclasses.asdict(
            ZGWConfigImport(
                total_rows_processed=5,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_informatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                zaak_resultaat_type_configs_imported=0,
                import_errors=[expected_error],
            ),
        )
        import_result["import_errors"][0] = str(import_result["import_errors"][0])
        import_expected["import_errors"][0] = str(import_expected["import_errors"][0])

        # check import
        self.assertEqual(import_result, import_expected)

    def test_import_jsonl_update_reports_duplicate_natural_keys_in_upload_file(self):
        mocks = ZGWExportImportMockData(with_dupes=True)

        self.storage.save("import.jsonl", io.StringIO(self.jsonl_with_dupes))

        # we use `asdict` and replace the Exceptions with string representations
        # because for Exceptions raised from within dataclasses, equality ==/is identity
        import_result = dataclasses.asdict(
            ZGWConfigImport.import_from_jsonl_file_in_django_storage(
                "import.jsonl", self.storage
            )
        )
        expected_error = ZGWImportError(
            "ZaakTypeStatusTypeConfig was processed multiple times because it contains duplicate "
            "natural keys: omschrijving = 'status omschrijving', ZaakTypeConfig identificatie = 'ztc-id-a-0'"
        )
        import_expected = dataclasses.asdict(
            ZGWConfigImport(
                total_rows_processed=7,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_informatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                # resultaat_type_config with "status omschrijving" should be imported
                zaak_resultaat_type_configs_imported=2,
                import_errors=[expected_error],
            ),
        )
        import_result["import_errors"][0] = str(import_result["import_errors"][0])
        import_expected["import_errors"][0] = str(import_expected["import_errors"][0])

        # check import
        self.assertEqual(import_result, import_expected)

    def test_import_jsonl_fails_with_catalogus_domein_rsin_mismatch(self):
        service = ServiceFactory(slug="service-0")
        CatalogusConfigFactory(
            url="https://foo.0.maykinmedia.nl",
            domein="FOO",
            rsin="123456789",
            service=service,
        )
        import_lines = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "BAR", "rsin": "987654321", "service": ["service-0"]}}',
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.0.maykinmedia.nl\\"]", "catalogus": ["DM-0", "123456789"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
        ]
        import_line = "\n".join(import_lines)

        with self.assertLogs(
            logger="open_inwoner.openzaak.import_export", level="ERROR"
        ) as cm:
            import_result = ZGWConfigImport.from_jsonl_stream_or_string(import_line)
            self.assertEqual(
                cm.output,
                [
                    # error from trying to load existing CatalogusConfig
                    "ERROR:open_inwoner.openzaak.import_export:"
                    "CatalogusConfig not found in target environment: Domein = 'BAR', Rsin = '987654321'",
                    # error from deserializing nested ZGW objects
                    "ERROR:open_inwoner.openzaak.import_export:"
                    "ZaakTypeConfig not found in target environment: Identificatie = 'ztc-id-a-0', Catalogus domein = 'DM-0', Catalogus rsin = '123456789'",
                ],
            )

        self.assertEqual(CatalogusConfig.objects.count(), 1)

        self.assertEqual(import_result.catalogus_configs_imported, 0)
        self.assertEqual(import_result.total_rows_processed, 2)

        self.assertEqual(
            list(CatalogusConfig.objects.values_list("url", "domein", "rsin")),
            [("https://foo.0.maykinmedia.nl", "FOO", "123456789")],
            msg="Value of sole CatalogusConfig matches imported values, not original values",
        )

    def test_bad_import_types(self):
        for bad_type in (set(), list(), b""):
            with self.assertRaises(ValueError):
                ZGWConfigImport.from_jsonl_stream_or_string(bad_type)

    def test_valid_input_types_are_accepted(self):
        ZGWExportImportMockData()

        for input in (
            io.StringIO(self.jsonl),
            io.BytesIO(self.jsonl.encode("utf-8")),
            self.jsonl,
        ):
            with self.subTest(f"Input type {type(input)}"):
                import_result = ZGWConfigImport.from_jsonl_stream_or_string(input)
                self.assertEqual(
                    import_result,
                    ZGWConfigImport(
                        total_rows_processed=5,
                        catalogus_configs_imported=1,
                        zaaktype_configs_imported=1,
                        zaak_informatie_object_type_configs_imported=1,
                        zaak_status_type_configs_imported=1,
                        zaak_resultaat_type_configs_imported=1,
                        import_errors=[],
                    ),
                )

    def test_import_is_atomic(self):
        bad_line = '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {}}\n'
        bad_jsonl = self.jsonl + "\n" + bad_line

        with self.assertRaises(KeyError):
            ZGWConfigImport.from_jsonl_stream_or_string(stream_or_string=bad_jsonl)

        counts = (
            CatalogusConfig.objects.count(),
            ZaakTypeConfig.objects.count(),
            ZaakTypeInformatieObjectTypeConfig.objects.count(),
            ZaakTypeStatusTypeConfig.objects.count(),
            ZaakTypeResultaatTypeConfig.objects.count(),
        )
        expected_counts = (0, 0, 0, 0, 0)

        self.assertEqual(
            counts,
            expected_counts,
            msg="Import should have merged, and not created new values",
        )


class ImportExportTestCase(TestCase):
    def setUp(self):
        ZGWExportImportMockData()

    def test_exports_can_be_imported(self):
        export = ZGWConfigExport.from_catalogus_configs(CatalogusConfig.objects.all())
        import_result = ZGWConfigImport.from_jsonl_stream_or_string(export.as_jsonl())

        self.assertEqual(import_result.total_rows_processed, 5)
