import io

from django.core.files.storage.memory import InMemoryStorage
from django.test import TestCase

from open_inwoner.openzaak.import_export import (
    CatalogusConfigExport,
    CatalogusConfigImport,
)
from open_inwoner.openzaak.models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)

from .factories import (
    CatalogusConfigFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
    ZaakTypeResultaatTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)


class ZGWExportImportMockData:
    def __init__(self, count=0):
        self.service = ServiceFactory(slug=f"service-{count}")
        self.catalogus = CatalogusConfigFactory(
            url=f"https://foo.{count}.maykinmedia.nl",
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
            urls=[f"https://foo.{count}.maykinmedia.nl"],
        )
        self.ztc_status = ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=self.ztc,
            statustype_url=f"https://foo.{count}.maykinmedia.nl",
            omschrijving="status omschrijving",
            statustekst="",
            zaaktype_uuids=[],
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
            resultaattype_url=f"https://foo.{count}.maykinmedia.nl",
            omschrijving="resultaat",
            zaaktype_uuids=[],
            description="",
        )
        self.ztiotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=self.ztc,
            informatieobjecttype_url=f"http://foo.{count}.maykinmedia.nl",
            omschrijving="informatieobject",
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
                    CatalogusConfigExport.from_catalogus_configs(arg)

    def test_export_only_accepts_queryset_of_correct_type(self):
        with self.assertRaises(ValueError):
            CatalogusConfigExport.from_catalogus_configs(ZaakTypeConfig.objects.all())

    def test_equality_operator(self):
        export_a = CatalogusConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[0].catalogus.pk)
        )
        export_b = CatalogusConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[1].catalogus.pk)
        )

        self.assertTrue(export_a == export_a)
        self.assertTrue(export_b == export_b)
        self.assertFalse(export_a == export_b)

    def test_only_models_related_to_exported_catalogus_config_are_included(self):
        export = CatalogusConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.filter(pk=self.mocks[0].catalogus.pk)
        )

        for export_field, mock_field in zip(
            (
                "catalogus_configs",
                "zaak_type_configs",
                "zaak_informatie_object_type_configs",
                "zaak_status_type_configs",
                "zaak_resultaat_type_configs",
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


class TestCatalogusExport(TestCase):
    def setUp(self):
        self.mocks = [
            ZGWExportImportMockData(0),
            ZGWExportImportMockData(1),
        ]

    def test_export_catalogus_configs(self):
        export = CatalogusConfigExport.from_catalogus_configs(
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
                    "catalogus": ["https://foo.0.maykinmedia.nl"],
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
                    "zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"],
                    "informatieobjecttype_url": "http://foo.0.maykinmedia.nl",
                    "omschrijving": "informatieobject",
                    "zaaktype_uuids": "[]",
                    "document_upload_enabled": False,
                    "document_notification_enabled": False,
                },
            },
            {
                "model": "openzaak.zaaktypestatustypeconfig",
                "fields": {
                    "zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"],
                    "statustype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "status omschrijving",
                    "statustekst": "",
                    "zaaktype_uuids": "[]",
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
                    "zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"],
                    "resultaattype_url": "https://foo.0.maykinmedia.nl",
                    "omschrijving": "resultaat",
                    "zaaktype_uuids": "[]",
                    "description": "",
                },
            },
        ]

        self.assertEqual(rows, expected)

    def test_export_catalogus_configs_as_jsonl(self):
        export = CatalogusConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.all()
        )
        rows = list(export.as_jsonl_iter())

        expected = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
            "\n",
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.1.maykinmedia.nl", "domein": "DM-1", "rsin": "123456789", "service": ["service-1"]}}',
            "\n",
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.0.maykinmedia.nl\\"]", "catalogus": ["https://foo.0.maykinmedia.nl"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            "\n",
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.1.maykinmedia.nl\\"]", "catalogus": ["https://foo.1.maykinmedia.nl"], "identificatie": "ztc-id-a-1", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            "\n",
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"], "informatieobjecttype_url": "http://foo.0.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            "\n",
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "https://foo.1.maykinmedia.nl"], "informatieobjecttype_url": "http://foo.1.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            "\n",
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"], "statustype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            "\n",
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "https://foo.1.maykinmedia.nl"], "statustype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            "\n",
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"], "resultaattype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[]", "description": ""}}',
            "\n",
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "https://foo.1.maykinmedia.nl"], "resultaattype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[]", "description": ""}}',
            "\n",
        ]

        self.assertEqual(rows, expected)


class TestCatalogusImport(TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.service = ServiceFactory(
            slug="service-0", api_root="https://foo.0.maykinmedia.nl"
        )
        self.other_service = ServiceFactory(
            slug="service-1", api_root="https://foo.1.maykinmedia.nl"
        )

        self.json_lines = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.1.maykinmedia.nl", "domein": "DM-1", "rsin": "123456789", "service": ["service-1"]}}',
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.0.maykinmedia.nl\\"]", "catalogus": ["https://foo.0.maykinmedia.nl"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.1.maykinmedia.nl\\"]", "catalogus": ["https://foo.1.maykinmedia.nl"], "identificatie": "ztc-id-a-1", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"], "informatieobjecttype_url": "http://foo.0.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "https://foo.1.maykinmedia.nl"], "informatieobjecttype_url": "http://foo.1.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"], "statustype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "https://foo.1.maykinmedia.nl"], "statustype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "https://foo.0.maykinmedia.nl"], "resultaattype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[]", "description": ""}}',
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-1", "https://foo.1.maykinmedia.nl"], "resultaattype_url": "https://foo.1.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[]", "description": ""}}',
        ]
        self.jsonl = "\n".join(self.json_lines)

    def test_import_jsonl_creates_objects(self):
        self.storage.save("import.jsonl", io.StringIO(self.jsonl))

        import_result = CatalogusConfigImport.import_from_jsonl_file_in_django_storage(
            "import.jsonl", self.storage
        )
        self.assertEqual(
            import_result,
            CatalogusConfigImport(
                total_rows_processed=10,
                catalogus_configs_imported=2,
                zaaktype_configs_imported=2,
                zaak_inormatie_object_type_configs_imported=2,
                zaak_status_type_configs_imported=2,
                zaak_resultaat_type_configs_imported=2,
            ),
        )

        self.assertEqual(CatalogusConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 2)
        self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 2)

    def test_import_jsonl_merges_objects(self):
        CatalogusConfigFactory(
            url="https://foo.0.maykinmedia.nl",
            domein="FOO",
            rsin="123456789",
            service=self.service,
        )
        merge_line = '{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "BAR", "rsin": "987654321", "service": ["service-0"]}}'

        import_result = CatalogusConfigImport.from_jsonl_stream_or_string(merge_line)

        self.assertEqual(import_result.catalogus_configs_imported, 1)
        self.assertEqual(import_result.total_rows_processed, 1)

        self.assertEqual(
            list(CatalogusConfig.objects.values_list("url", "domein", "rsin")),
            [("https://foo.0.maykinmedia.nl", "BAR", "987654321")],
            msg="Value of sole CatalogusConfig matches imported values, not original values",
        )

    def test_bad_import_types(self):
        for bad_type in (set(), list(), b""):
            with self.assertRaises(ValueError):
                CatalogusConfigImport.from_jsonl_stream_or_string(bad_type)

    def test_valid_input_types_are_accepted(self):
        for input in (
            io.StringIO(self.jsonl),
            io.BytesIO(self.jsonl.encode("utf-8")),
            self.jsonl,
        ):
            with self.subTest(f"Input type {type(input)}"):
                import_result = CatalogusConfigImport.from_jsonl_stream_or_string(input)
                self.assertEqual(
                    import_result,
                    CatalogusConfigImport(
                        total_rows_processed=10,
                        catalogus_configs_imported=2,
                        zaaktype_configs_imported=2,
                        zaak_inormatie_object_type_configs_imported=2,
                        zaak_status_type_configs_imported=2,
                        zaak_resultaat_type_configs_imported=2,
                    ),
                )

                self.assertEqual(CatalogusConfig.objects.count(), 2)
                self.assertEqual(ZaakTypeConfig.objects.count(), 2)
                self.assertEqual(ZaakTypeInformatieObjectTypeConfig.objects.count(), 2)
                self.assertEqual(ZaakTypeStatusTypeConfig.objects.count(), 2)
                self.assertEqual(ZaakTypeResultaatTypeConfig.objects.count(), 2)

    def test_import_is_atomic(self):
        bad_line = '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {}}\n'
        bad_jsonl = self.jsonl + "\n" + bad_line

        try:
            CatalogusConfigImport.from_jsonl_stream_or_string(
                stream_or_string=bad_jsonl
            )
        except Exception:
            pass

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


class RewriteUrlsImportTests(TestCase):
    def setUp(self):
        self.service = ServiceFactory(
            slug="constant-api-slug", api_root="http://one.maykinmedia.nl"
        )

        import_lines = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "http://one.maykinmedia.nl/catalogus/1", "domein": "ALLE", "rsin": "1234568", "service": ["constant-api-slug"]}}',
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"http://one.maykinmedia.nl/types/1\\", \\"http://one.maykinmedia.nl/types/2\\"]", "catalogus": ["http://one.maykinmedia.nl/catalogus/1"], "identificatie": "zt-1", "omschrijving": "iGsHCEkCpEJyDLeAaytskGiAXSAPVVthCvOdbNdpZZcCciXFnZGltXFYsYigSkIZiaqMEvSPftMgIYyW", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["zt-1", "http://one.maykinmedia.nl/catalogus/1"], "informatieobjecttype_url": "http://one.maykinmedia.nl/iotype/1", "omschrijving": "IzNqfWpVpbyMEjSXTqQUlslqAUYFdILFlSDAelAkfTROWptqgIRCmaIoWCBMBAozsJLWxGoJqmBLPCHy", "zaaktype_uuids": "[]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["zt-1", "http://one.maykinmedia.nl/catalogus/1"], "statustype_url": "http://one.maykinmedia.nl/status-type/1", "omschrijving": "BHEJLQkSTdMPGtSzgnIbIdhMvFiNOBHmFQkRvLxHUkmafelprqCpcuAZzqMWBLgqNkGmXpzWPjhWqKjk", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["zt-1", "http://one.maykinmedia.nl/catalogus/1"], "resultaattype_url": "http://one.maykinmedia.nl/resultaat-type/1", "omschrijving": "", "zaaktype_uuids": "[]", "description": ""}}',
        ]
        self.jsonl = "\n".join(import_lines)

    def _create_fixtures(self, base_url: str):
        catalogus = CatalogusConfigFactory(
            url=f"{base_url}/catalogus/1",
            service=self.service,
            domein="ALLE",
            rsin="1234568",
        )
        zt = ZaakTypeConfigFactory(
            catalogus=catalogus,
            identificatie="zt-1",
            urls=[
                f"{base_url}/types/1",
                f"{base_url}/types/2",
            ],
        )
        ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zt,
            informatieobjecttype_url=f"{base_url}/iotype/1",
        )
        ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=zt, statustype_url=f"{base_url}/status-type/1"
        )
        ZaakTypeResultaatTypeConfigFactory(
            zaaktype_config=zt,
            resultaattype_url=f"{base_url}/resultaat-type/1",
        )

    def test_jsonl_url_rewrite(self):
        self.service.api_root = "http://two.maykinmedia.nl"
        self.service.save()

        rewritten_lines = list(
            CatalogusConfigImport._rewrite_jsonl_url_references(self.jsonl)
        )
        expected_lines = [
            '{"model": "openzaak.catalogusconfig", "fields": {"url": "http://two.maykinmedia.nl/catalogus/1", "domein": "ALLE", "rsin": "1234568", "service": ["constant-api-slug"]}}',
            '{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"http://two.maykinmedia.nl/types/1\\", \\"http://two.maykinmedia.nl/types/2\\"]", "catalogus": ["http://two.maykinmedia.nl/catalogus/1"], "identificatie": "zt-1", "omschrijving": "iGsHCEkCpEJyDLeAaytskGiAXSAPVVthCvOdbNdpZZcCciXFnZGltXFYsYigSkIZiaqMEvSPftMgIYyW", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": false, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            '{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["zt-1", "http://two.maykinmedia.nl/catalogus/1"], "informatieobjecttype_url": "http://two.maykinmedia.nl/iotype/1", "omschrijving": "IzNqfWpVpbyMEjSXTqQUlslqAUYFdILFlSDAelAkfTROWptqgIRCmaIoWCBMBAozsJLWxGoJqmBLPCHy", "zaaktype_uuids": "[]", "document_upload_enabled": false, "document_notification_enabled": false}}',
            '{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["zt-1", "http://two.maykinmedia.nl/catalogus/1"], "statustype_url": "http://two.maykinmedia.nl/status-type/1", "omschrijving": "BHEJLQkSTdMPGtSzgnIbIdhMvFiNOBHmFQkRvLxHUkmafelprqCpcuAZzqMWBLgqNkGmXpzWPjhWqKjk", "statustekst": "", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            '{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["zt-1", "http://two.maykinmedia.nl/catalogus/1"], "resultaattype_url": "http://two.maykinmedia.nl/resultaat-type/1", "omschrijving": "", "zaaktype_uuids": "[]", "description": ""}}',
        ]

        self.assertEqual(
            rewritten_lines,
            expected_lines,
            msg="All URLs should be rewritten to match the target service root",
        )

    def test_rewrite_target_diverges_from_existing_objects(self):
        self._create_fixtures("http://one.maykinmedia.nl/")
        self.service.api_root = "http://two.maykinmedia.nl"
        self.service.save()

        import_result = CatalogusConfigImport.from_jsonl_stream_or_string(self.jsonl)

        self.assertEqual(
            import_result,
            CatalogusConfigImport(
                total_rows_processed=5,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_inormatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                zaak_resultaat_type_configs_imported=1,
            ),
        )

        counts = (
            CatalogusConfig.objects.count(),
            ZaakTypeConfig.objects.count(),
            ZaakTypeInformatieObjectTypeConfig.objects.count(),
            ZaakTypeStatusTypeConfig.objects.count(),
            ZaakTypeResultaatTypeConfig.objects.count(),
        )
        expected_counts = (2, 2, 2, 2, 2)

        self.assertEqual(
            counts,
            expected_counts,
            msg="Import should have merged, and not created new values",
        )

    def test_rewrite_target_matches_from_existing_objects(self):
        self.service.api_root = "http://two.maykinmedia.nl"
        self.service.save()
        self._create_fixtures("http://two.maykinmedia.nl")

        import_result = CatalogusConfigImport.from_jsonl_stream_or_string(self.jsonl)
        self.assertEqual(
            import_result,
            CatalogusConfigImport(
                total_rows_processed=5,
                catalogus_configs_imported=1,
                zaaktype_configs_imported=1,
                zaak_inormatie_object_type_configs_imported=1,
                zaak_status_type_configs_imported=1,
                zaak_resultaat_type_configs_imported=1,
            ),
        )

        counts = (
            CatalogusConfig.objects.count(),
            ZaakTypeConfig.objects.count(),
            ZaakTypeInformatieObjectTypeConfig.objects.count(),
            ZaakTypeStatusTypeConfig.objects.count(),
            ZaakTypeResultaatTypeConfig.objects.count(),
        )
        expected_counts = (1, 1, 1, 1, 1)

        self.assertEqual(
            counts,
            expected_counts,
            msg="Import should have merged, and not created new values",
        )


class ImportExportTestCase(TestCase):
    def setUp(self):
        ZGWExportImportMockData()

    def test_exports_can_be_imported(self):
        export = CatalogusConfigExport.from_catalogus_configs(
            CatalogusConfig.objects.all()
        )
        import_result = CatalogusConfigImport.from_jsonl_stream_or_string(
            export.as_jsonl()
        )

        self.assertEqual(import_result.total_rows_processed, 5)
