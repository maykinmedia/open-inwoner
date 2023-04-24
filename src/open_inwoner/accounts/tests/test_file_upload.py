from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from privates.test import temp_private_root
from webtest import Upload

from open_inwoner.accounts.models import Action, Message

from .factories import UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestActionFileUploadLimits(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.response = self.app.get(reverse("profile:action_create"), user=self.user)
        self.form = self.response.forms["action-create"]

    @temp_private_root()
    def test_valid_type_of_file_is_uploaded(self):

        self.form["file"] = Upload("readme.xlsx", b"data", "application/vnd.ms-excel")
        self.form["name"] = "Action name"
        upload_response = self.form.submit()
        self.assertEquals(Action.objects.first().file.name, "readme.xlsx")
        self.assertRedirects(upload_response, reverse("profile:action_list"))

    @temp_private_root()
    def test_invalid_type_of_file_is_not_uploaded(self):
        self.form["file"] = Upload("readme.svg", b"data", "image/svg+xml")
        self.form["name"] = "readme"
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: pdf, docx, doc, xlsx, xls, jpeg, jpg, png, txt, odt, odf, ods"
                )
            ],
        )

    @override_settings(MAX_UPLOAD_SIZE=2)
    @temp_private_root()
    def test_files_bigger_than_max_size_are_not_uploaded(self):
        self.form["file"] = Upload("readme.png", b"data", "image/png")
        self.form["name"] = "readme"
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Een aangeleverd bestand dient maximaal {size} te zijn, uw bestand is te groot."
                ).format(size=filesizeformat(settings.MAX_UPLOAD_SIZE))
            ],
        )

    @override_settings(MIN_UPLOAD_SIZE=20)
    @temp_private_root()
    def test_files_smaller_than_min_size_are_not_uploaded(self):
        self.form["file"] = Upload("readme.png", b"data", "image/png")
        self.form["name"] = "readme"
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Een aangeleverd bestand dient minimaal {size} te zijn, uw bestand is te klein."
                ).format(size=filesizeformat(settings.MIN_UPLOAD_SIZE))
            ],
        )

    @temp_private_root()
    def test_files_with_no_content_are_not_uploaded(self):
        self.form["file"] = Upload("readme.png", b"", "image/png")
        self.form["name"] = "readme"
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"], [_("Het verstuurde bestand is leeg.")]
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestMessageFileUploadLimits(WebTest):
    def setUp(self):
        self.me = UserFactory()
        self.contact = UserFactory()
        self.me.user_contacts.add(self.contact)
        self.response = self.app.get(reverse("inbox:start"), user=self.me)
        self.form = self.response.forms["start-message-form"]

    @temp_private_root()
    def test_valid_type_of_file_is_uploaded(self):
        self.form["file"] = Upload("readme.xlsx", b"data", "application/vnd.ms-excel")
        self.form["content"] = "The message content"
        self.form["receiver"] = str(self.contact.uuid)
        upload_response = self.form.submit()
        self.assertEquals(Message.objects.first().file.name, "readme.xlsx")
        self.assertRedirects(
            upload_response,
            reverse("inbox:index", kwargs={"uuid": self.contact.uuid})
            + "#messages-last",
            fetch_redirect_response=False,
        )

    @temp_private_root()
    def test_invalid_type_of_file_is_not_uploaded(self):
        self.form["file"] = Upload("readme.svg", b"data", "image/svg+xml")
        self.form["content"] = "The message content"
        self.form["receiver"] = str(self.contact.uuid)
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: pdf, docx, doc, xlsx, xls, jpeg, jpg, png, txt, odt, odf, ods"
                )
            ],
        )

    @override_settings(MAX_UPLOAD_SIZE=2)
    @temp_private_root()
    def test_files_bigger_than_max_size_are_not_uploaded(self):
        self.form["file"] = Upload("readme.png", b"data", "image/png")
        self.form["content"] = "The message content"
        self.form["receiver"] = str(self.contact.uuid)
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Een aangeleverd bestand dient maximaal {size} te zijn, uw bestand is te groot."
                ).format(size=filesizeformat(settings.MAX_UPLOAD_SIZE))
            ],
        )

    @override_settings(MIN_UPLOAD_SIZE=20)
    @temp_private_root()
    def test_files_smaller_than_min_size_are_not_uploaded(self):
        self.form["file"] = Upload("readme.png", b"data", "image/png")
        self.form["content"] = "The message content"
        self.form["receiver"] = str(self.contact.uuid)
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"],
            [
                _(
                    "Een aangeleverd bestand dient minimaal {size} te zijn, uw bestand is te klein."
                ).format(size=filesizeformat(settings.MIN_UPLOAD_SIZE))
            ],
        )

    @temp_private_root()
    def test_files_with_no_content_are_not_uploaded(self):
        self.form["file"] = Upload("readme.png", b"", "image/png")
        self.form["content"] = "The message content"
        self.form["receiver"] = str(self.contact.uuid)
        upload_response = self.form.submit()
        self.assertEquals(
            upload_response.context["errors"], [_("Het verstuurde bestand is leeg.")]
        )
