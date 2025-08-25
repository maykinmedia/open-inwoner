from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import SiteConfiguration


@disable_admin_mfa()
class TestAdminSite(WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True, is_staff=True)

    def test_site_add_prevented_if_one_exists(self):
        """Test that adding a site is prevented if one already exists."""
        # Make sure we have exactly one site
        initial_site_count = Site.objects.count()
        self.assertEqual(initial_site_count, 1)

        response = self.app.get(
            reverse("admin:sites_site_add"), user=self.user, expect_errors=True
        )

        self.assertEqual(response.status_code, 403)

        self.assertEqual(Site.objects.count(), initial_site_count)

    def test_site_deletion_prevented(self):
        """Test that site deletion is prevented."""
        site = Site.objects.get()

        response = self.app.get(
            reverse("admin:sites_site_change", args=[site.pk]), user=self.user
        )

        # Verify the delete button is not present (text or link)
        self.assertNotIn("Delete", response.text)
        delete_url = reverse("admin:sites_site_delete", args=[site.pk])
        self.assertNotIn(delete_url, response.text)

        # Try to access the delete page directly - should return 403 Forbidden
        response = self.app.get(delete_url, user=self.user, expect_errors=True)
        self.assertEqual(response.status_code, 403)

        # Verify the site still exists
        self.assertTrue(Site.objects.filter(pk=site.pk).exists())


@disable_admin_mfa()
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
        # django-jsonform requires JS to work properly and with Webtest the default
        # value for ArrayFields is an empty string, causing it crash to when trying to parse
        # that value as JSON
        self.form["recipients_email_digest"] = "[]"

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
