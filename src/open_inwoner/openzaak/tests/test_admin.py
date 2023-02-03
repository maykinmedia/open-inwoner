from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import ZaakTypeConfigFactory, ZaakTypeInformatieObjectTypeConfigFactory


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
