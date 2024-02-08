from django.urls import reverse

from django_webtest import WebTest
from webtest import Upload

from open_inwoner.accounts.tests.factories import UserFactory

from ...utils.test import ClearCachesMixin
from ..models import CustomFontSet, SiteConfiguration


class CustomFontsTest(ClearCachesMixin, WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)

        self.config = SiteConfiguration.get_solo()
        self.config.custom_fonts = CustomFontSet()
        self.config.save()

        self.form = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"), user=self.user
        ).forms["siteconfiguration_form"]

    def test_upload_font_correct_filetype(self):
        font_file = Upload("valid.ttf", b"content", content_type="font/ttf")
        self.form["name"] = "Test"
        self.form["custom_fonts-0-body_font_regular"] = font_file
        self.form["custom_fonts-0-body_font_bold"] = font_file
        self.form["custom_fonts-0-body_font_italic"] = font_file
        self.form["custom_fonts-0-body_font_bold_italic"] = font_file
        self.form["custom_fonts-0-heading_font"] = font_file

        self.form.submit()

        custom_font_set = CustomFontSet.objects.first()
        body_font = custom_font_set.body_font_regular
        body_font_bold = custom_font_set.body_font_bold
        body_font_italic = custom_font_set.body_font_italic
        body_font_bold_italic = custom_font_set.body_font_bold_italic
        heading_font = custom_font_set.heading_font

        self.assertEqual(body_font.name, "custom_fonts/body_font_regular.ttf")
        self.assertEqual(body_font_bold.name, "custom_fonts/body_font_bold.ttf")
        self.assertEqual(body_font_italic.name, "custom_fonts/body_font_italic.ttf")
        self.assertEqual(
            body_font_bold_italic.name, "custom_fonts/body_font_bold_italic.ttf"
        )
        self.assertEqual(heading_font.name, "custom_fonts/heading_font.ttf")

        # test file overwrite: upload again
        another_font_file = Upload(
            "valid_encore.ttf", b"content", content_type="font/ttf"
        )
        self.form["custom_fonts-0-body_font_regular"] = another_font_file
        self.form["custom_fonts-0-heading_font"] = another_font_file

        self.form.submit()

        self.assertEqual(len(CustomFontSet.objects.all()), 1)

        custom_font_set = CustomFontSet.objects.first()
        body_font = custom_font_set.body_font_regular
        heading_font = custom_font_set.heading_font

        self.assertEqual(body_font.name, "custom_fonts/body_font_regular.ttf")
        self.assertEqual(heading_font.name, "custom_fonts/heading_font.ttf")

    def test_upload_font_incorrect_filetype(self):
        font_file = Upload("invalid.svg", b"content", content_type="font/svg")
        self.form["name"] = "Test"
        self.form["custom_fonts-0-body_font_regular"] = font_file

        response = self.form.submit()

        self.assertEquals(
            response.context["errors"],
            [
                [
                    "Bestandsextensie ‘svg’ is niet toegestaan. Toegestane extensies zijn: ‘ttf’."
                ]
            ],
        )
