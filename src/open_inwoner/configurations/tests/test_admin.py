from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import SiteConfiguration


class TestAdminForm(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.form = self.app.get(
            reverse("admin:configurations_siteconfiguration_change"), user=self.user
        ).forms["siteconfiguration_form"]
        self.form["name"] = "xyz"
        self.form["primary_color"] = "#FFFFFF"
        self.form["primary_font_color"] = "#FFFFFF"
        self.form["secondary_color"] = "#FFFFFF"
        self.form["secondary_font_color"] = "#FFFFFF"
        self.form["accent_color"] = "#FFFFFF"
        self.form["accent_font_color"] = "#FFFFFF"

    def test_valid_path_is_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "/accounts/login/"
        self.form.submit()

        config.refresh_from_db()

        self.assertEqual(config.redirect_to, "/accounts/login/")

    def test_invalid_path_is_not_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "/invalid/path"
        response = self.form.submit()

        config.refresh_from_db()

        self.assertIsNone(config.redirect_to)
        self.assertEqual(
            response.context["errors"], [[_("The entered path is invalid.")]]
        )

    def test_valid_url_is_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "https://www.example.com"
        self.form.submit()

        config.refresh_from_db()

        self.assertEqual(config.redirect_to, "https://www.example.com")

    def test_invalid_url_is_not_saved(self):
        config = SiteConfiguration.get_solo()
        self.assertIsNone(config.redirect_to)

        self.form["redirect_to"] = "invalid-url.com"
        response = self.form.submit()

        config.refresh_from_db()

        self.assertIsNone(config.redirect_to)
        self.assertEqual(
            response.context["errors"], [[_("The entered url is invalid.")]]
        )
