import html
import json
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import freezegun
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from privates.storages import PrivateMediaFileSystemStorage
from privates.test import temp_private_root
from webtest import Upload

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import (
    CatalogusConfigFactory,
    ServiceFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)


@disable_admin_mfa()
class TestZaakTypeConfigAdmin(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.ztc = ZaakTypeConfigFactory()
        self.ztiotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=self.ztc
        )

    def test_enabling_only_ztc_succeeds(self):

        response = self.app.get(
            reverse(
                "admin:openzaak_zaaktypeconfig_change",
                kwargs={"object_id": self.ztc.id},
            ),
            user=self.user,
        )
        form = response.forms["zaaktypeconfig_form"]
        form["document_upload_enabled"] = True
        form_response = form.submit("_save")

        self.ztc.refresh_from_db()
        self.ztiotc.refresh_from_db()

        self.assertRedirects(
            form_response, reverse("admin:openzaak_zaaktypeconfig_changelist")
        )
        self.assertTrue(self.ztc.document_upload_enabled)
        self.assertFalse(self.ztiotc.document_upload_enabled)

    def test_enabling_only_ztiotc_succeeds(self):

        response = self.app.get(
            reverse(
                "admin:openzaak_zaaktypeconfig_change",
                kwargs={"object_id": self.ztc.id},
            ),
            user=self.user,
        )
        form = response.forms["zaaktypeconfig_form"]
        form["zaaktypeinformatieobjecttypeconfig_set-0-document_upload_enabled"] = True
        form_response = form.submit("_save")

        self.ztc.refresh_from_db()
        self.ztiotc.refresh_from_db()

        self.assertRedirects(
            form_response, reverse("admin:openzaak_zaaktypeconfig_changelist")
        )
        self.assertFalse(self.ztc.document_upload_enabled)
        self.assertTrue(self.ztiotc.document_upload_enabled)

    def test_enabling_both_upload_types_fails(self):
        response = self.app.get(
            reverse(
                "admin:openzaak_zaaktypeconfig_change",
                kwargs={"object_id": self.ztc.id},
            ),
            user=self.user,
        )
        form = response.forms["zaaktypeconfig_form"]
        form["document_upload_enabled"] = True
        form["zaaktypeinformatieobjecttypeconfig_set-0-document_upload_enabled"] = True
        form_response = form.submit("_save")

        expected_error = [
            _(
                "Enabling both zaaktype and zaaktypeinformatieobject upload is not allowed. Only one of them should be enabled."
            )
        ]

        self.ztc.refresh_from_db()
        self.ztiotc.refresh_from_db()

        self.assertEqual(form_response.context["errors"], expected_error)
        self.assertFalse(self.ztc.document_upload_enabled)
        self.assertFalse(self.ztiotc.document_upload_enabled)

    def test_both_can_be_disabled(self):
        response = self.app.get(
            reverse(
                "admin:openzaak_zaaktypeconfig_change",
                kwargs={"object_id": self.ztc.id},
            ),
            user=self.user,
        )
        form = response.forms["zaaktypeconfig_form"]
        form["document_upload_enabled"] = False
        form["zaaktypeinformatieobjecttypeconfig_set-0-document_upload_enabled"] = False
        form_response = form.submit("_save")

        self.ztc.refresh_from_db()
        self.ztiotc.refresh_from_db()

        self.assertRedirects(
            form_response, reverse("admin:openzaak_zaaktypeconfig_changelist")
        )
        self.assertFalse(self.ztc.document_upload_enabled)
        self.assertFalse(self.ztiotc.document_upload_enabled)


@disable_admin_mfa()
@temp_private_root()
@freezegun.freeze_time("2024-08-14 17:50:01")
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestCatalogusConfigExportAdmin(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.service = ServiceFactory(slug="service-1")
        self.catalogus = CatalogusConfigFactory(
            url="https://foo.maykinmedia.nl",
            domein="DM",
            rsin="123456789",
            service=self.service,
        )
        self.mock_file = Upload("dump.json", b"foobar", "application/json")

    def test_export_action_returns_correct_export(self):
        response = self.app.post(
            reverse(
                "admin:openzaak_catalogusconfig_changelist",
            ),
            {
                "action": "export_catalogus_configs",
                "_selected_action": [self.catalogus.id],
            },
            user=self.user,
        )

        self.assertEqual(
            response.content_disposition,
            'attachment; filename="zgw-catalogi-export.json"',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [json.loads(row) for row in response.text.split("\n")[:-1]],
            [
                {
                    "model": "openzaak.catalogusconfig",
                    "fields": {
                        "url": "https://foo.maykinmedia.nl",
                        "domein": "DM",
                        "rsin": "123456789",
                        "service": ["service-1"],
                    },
                },
            ],
            msg="Response should be valid JSONL matching the input object",
        )

    def test_import_flow_reports_success(self) -> None:
        service = ServiceFactory.create(slug="service-0")
        CatalogusConfigFactory.create(
            url="https://foo.0.maykinmedia.nl",
            domein="DM-0",
            rsin="123456789",
            service=service,
        )
        import_lines = [
            b'{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
        ]
        import_line = b"\n".join(import_lines)
        mock_file = Upload("dump.json", import_line, "application/json")

        form = self.app.get(
            reverse(
                "admin:upload_catalogus_import_file",
            ),
            user=self.user,
        ).form
        form["zgw_export_file"] = mock_file

        response = form.submit().follow()

        messages = [str(msg) for msg in response.context["messages"]]
        self.assertEqual(
            messages,
            [_("1 item(s) processed in total, with 0 failing row(s).")],
        )
        self.assertFalse(
            PrivateMediaFileSystemStorage().exists(
                "zgw_import_dump_2024-08-14-17-50-01.jsonl"
            ),
            msg="File should always be deleted regardless of success or failure",
        )
        self.assertEqual(
            response.request.path,
            reverse(
                "admin:openzaak_catalogusconfig_changelist",
            ),
        )

    @mock.patch(
        "open_inwoner.openzaak.import_export.ZGWConfigImport.import_from_jsonl_file_in_django_storage"
    )
    def test_import_flow_errors_reports_failure_to_user(self, m) -> None:
        m.side_effect = Exception("something went wrong")
        form = self.app.get(
            reverse(
                "admin:upload_catalogus_import_file",
            ),
            user=self.user,
        ).form
        form["zgw_export_file"] = self.mock_file

        response = form.submit()

        self.assertEqual(m.call_count, 1)
        self.assertEqual(m.call_args[0][0], "zgw_import_dump_2024-08-14-17-50-01.json")
        self.assertTrue(isinstance(m.call_args[0][1], PrivateMediaFileSystemStorage))

        messages = [str(msg) for msg in response.context["messages"]]
        self.assertEqual(
            messages,
            [
                _(
                    "We were unable to process your upload. Please regenerate the file and try again."
                )
            ],
        )
        self.assertFalse(
            PrivateMediaFileSystemStorage().exists(
                "zgw_import_dump_2024-08-14-17-50-01.json"
            ),
            msg="File should always be deleted regardless of success or failure",
        )
        self.assertEqual(
            response.request.path,
            reverse(
                "admin:upload_catalogus_import_file",
            ),
        )

    def test_import_flow_reports_errors(self) -> None:
        import_lines = [
            b'{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
            b'{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.0.maykinmedia.nl\\"]", "catalogus": ["DM-0", "123456789"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": true, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
            b'{"model": "openzaak.zaaktypeinformatieobjecttypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "informatieobjecttype_url": "http://foo.0.maykinmedia.nl", "omschrijving": "informatieobject", "zaaktype_uuids": "[]", "document_upload_enabled": true, "document_notification_enabled": true}}',
            b'{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "statustype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "status omschrijving", "statustekst": "statustekst nieuw", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
            b'{"model": "openzaak.zaaktyperesultaattypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "resultaattype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "resultaat", "zaaktype_uuids": "[]", "description": "description new"}}',
            b'{"model": "openzaak.zaaktypestatustypeconfig", "fields": {"zaaktype_config": ["ztc-id-a-0", "DM-0", "123456789"], "statustype_url": "https://foo.0.maykinmedia.nl", "omschrijving": "bogus", "statustekst": "bogus", "zaaktype_uuids": "[]", "status_indicator": "", "status_indicator_text": "", "document_upload_description": "", "description": "status", "notify_status_change": true, "action_required": false, "document_upload_enabled": true, "call_to_action_url": "", "call_to_action_text": "", "case_link_text": ""}}',
        ]
        import_line = b"\n".join(import_lines)
        mock_file = Upload("dump.json", import_line, "application/json")

        form = self.app.get(
            reverse(
                "admin:upload_catalogus_import_file",
            ),
            user=self.user,
        ).form
        form["zgw_export_file"] = mock_file

        response = form.submit().follow()

        messages = [html.unescape(str(msg)) for msg in response.context["messages"]]
        self.assertEqual(len(messages), 2)
        self.assertEqual(
            _("6 item(s) processed in total, with 6 failing row(s)."),
            messages[0],
        )
        self.assertIn(
            "ZaakTypeConfig not found in target environment: Identificatie = 'ztc-id-a-0', "
            "Catalogus domein = 'DM-0', Catalogus rsin = '123456789'",
            messages[1],
        )
        self.assertIn(
            "ZaakTypeStatusTypeConfig not found in target environment: omschrijving = 'bogus', "
            "ZaakTypeConfig identificatie = 'ztc-id-a-0'",
            messages[1],
        )
        self.assertIn(
            "ZaakTypeStatusTypeConfig not found in target environment: omschrijving = 'bogus', ZaakTypeConfig "
            "identificatie = 'ztc-id-a-0'",
            messages[1],
        )
        self.assertIn(
            "ZaakTypeInformatieObjectTypeConfig not found in target environment: omschrijving = 'informatieobject', "
            "ZaakTypeConfig identificatie = 'ztc-id-a-0'",
            messages[1],
        )
        self.assertIn(
            "CatalogusConfig not found in target environment: Domein = 'DM-0', Rsin = '123456789'",
            messages[1],
        )
        self.assertIn(
            "ZaakTypeResultaatTypeConfig not found in target environment: omschrijving = 'resultaat', "
            "ZaakTypeConfig identificatie = 'ztc-id-a-0'",
            messages[1],
        )

    def test_import_flow_reports_partial_errors(self) -> None:
        service = ServiceFactory.create(slug="service-0")
        CatalogusConfigFactory.create(
            url="https://foo.0.maykinmedia.nl",
            domein="DM-0",
            rsin="123456789",
            service=service,
        )
        import_lines = [
            b'{"model": "openzaak.catalogusconfig", "fields": {"url": "https://foo.0.maykinmedia.nl", "domein": "DM-0", "rsin": "123456789", "service": ["service-0"]}}',
            b'{"model": "openzaak.zaaktypeconfig", "fields": {"urls": "[\\"https://foo.0.maykinmedia.nl\\"]", "catalogus": ["DM-0", "123456789"], "identificatie": "ztc-id-a-0", "omschrijving": "zaaktypeconfig", "notify_status_changes": false, "description": "", "external_document_upload_url": "", "document_upload_enabled": true, "contact_form_enabled": false, "contact_subject_code": "", "relevante_zaakperiode": null}}',
        ]
        import_line = b"\n".join(import_lines)
        mock_file = Upload("dump.json", import_line, "application/json")

        form = self.app.get(
            reverse(
                "admin:upload_catalogus_import_file",
            ),
            user=self.user,
        ).form
        form["zgw_export_file"] = mock_file

        response = form.submit().follow()

        messages = [html.unescape(str(msg)) for msg in response.context["messages"]]
        self.assertEqual(len(messages), 2)
        self.assertEqual(
            _("2 item(s) processed in total, with 1 failing row(s)."),
            messages[0],
        )
        self.assertEqual(
            "It was not possible to import the following items:<div><p> - ZaakTypeConfig not found in target environment: Identificatie = 'ztc-id-a-0', Catalogus domein = 'DM-0', Catalogus rsin = '123456789'</p></div>",
            messages[1],
        )
