from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from privates.test import temp_private_root
from webtest import Upload

from open_inwoner.accounts.models import Document

from .factories import UserFactory


class TestFileUploadLimits(WebTest):
    def setUp(self):
        self.user = UserFactory()

    @temp_private_root()
    def test_valid_type_of_file_is_uploaded(self):
        response = self.app.get(reverse("accounts:documents_create"), user=self.user)
        response.forms["document-create"]["file"] = Upload(
            "readme.xlsx", b"data", "application/vnd.ms-excel"
        )
        response.forms["document-create"]["name"] = "readme"
        upload_response = response.forms["document-create"].submit()
        self.assertEquals(Document.objects.count(), 1)
        self.assertRedirects(upload_response, reverse("accounts:my_profile"))

    @temp_private_root()
    def test_invalid_type_of_file_is_not_uploaded(self):
        response = self.app.get(reverse("accounts:documents_create"), user=self.user)
        response.forms["document-create"]["file"] = Upload(
            "readme.svg", b"data", "image/svg+xml"
        )
        response.forms["document-create"]["name"] = "readme"
        upload_response = response.forms["document-create"].submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: docx, pdf, doc, xlsx, xls, jpeg, jpg, png, txt, odt, odf, ods"
                )
            ],
        )

    @override_settings(MAX_UPLOAD_SIZE=2)
    def test_files_bigger_than_max_size_are_not_uploaded(self):
        response = self.app.get(reverse("accounts:documents_create"), user=self.user)
        response.forms["document-create"]["file"] = Upload(
            "readme.png", b"data", "image/png"
        )
        response.forms["document-create"]["name"] = "readme"
        upload_response = response.forms["document-create"].submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Een aangeleverd bestand dient maximaal {size} te zijn, uw bestand is te groot."
                ).format(size=filesizeformat(settings.MAX_UPLOAD_SIZE))
            ],
        )

    @override_settings(MIN_UPLOAD_SIZE=20)
    def test_files_smaller_than_min_size_are_not_uploaded(self):
        response = self.app.get(reverse("accounts:documents_create"), user=self.user)
        response.forms["document-create"]["file"] = Upload(
            "readme.png", b"data", "image/png"
        )
        response.forms["document-create"]["name"] = "readme"
        upload_response = response.forms["document-create"].submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Een aangeleverd bestand dient minimaal {size} te zijn, uw bestand is te klein."
                ).format(size=filesizeformat(settings.MIN_UPLOAD_SIZE))
            ],
        )

    def test_files_with_no_content_are_not_uploaded(self):
        response = self.app.get(reverse("accounts:documents_create"), user=self.user)
        response.forms["document-create"]["file"] = Upload(
            "readme.png", b"", "image/png"
        )
        response.forms["document-create"]["name"] = "readme"
        upload_response = response.forms["document-create"].submit()
        self.assertEquals(
            upload_response.context["errors"], [_("Het verstuurde bestand is leeg.")]
        )
