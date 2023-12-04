from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import SiteConfiguration


class TestAdminSite(WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True, is_staff=True)

    def test_delete_site_success(self):
        site2 = Site.objects.create(id=2, domain="example2.com", name="example2")

        # delete site
        response = self.app.get(
            reverse("admin:sites_site_delete", kwargs={"object_id": site2.id}),
            user=self.user,
        )
        response = response.form.submit().follow()

        # check sites
        sites = Site.objects.all()
        self.assertEqual(len(sites), 1)

        # check message
        doc = PyQuery(response.content)

        success_msg = doc.find(".success").text()
        self.assertIn("met succes verwijderd.", success_msg)

    def test_delete_last_site_fail(self):
        # attempt to delete site
        response = self.app.get(
            reverse("admin:sites_site_delete", kwargs={"object_id": 1}), user=self.user
        )
        response = response.form.submit().follow()

        # check sites
        sites = Site.objects.all()
        self.assertEqual(len(sites), 1)

        # check message
        doc = PyQuery(response.content)

        warning_msg = doc.find(".warning").text()
        self.assertEqual(warning_msg, _("You cannot delete the last site."))

    def test_bulk_delete_success(self):
        site2 = Site.objects.create(id=2, domain="example2.com", name="example2")
        site3 = Site.objects.create(id=3, domain="example3.com", name="example3")

        # delete sites
        data = {"action": "delete_selected", "_selected_action": [site2.pk, site3.pk]}
        response = self.app.post(
            reverse("admin:sites_site_changelist"), data, user=self.user
        )
        response = response.form.submit().follow()  # confirmation form

        # check sites
        sites = Site.objects.all()
        self.assertEqual(len(sites), 1)

        # check message
        doc = PyQuery(response.content)

        success_msg = doc.find(".success").text()
        self.assertEqual(success_msg, "2 websites met succes verwijderd.")

    def test_bulk_delete_fail(self):
        Site.objects.create(id=2, domain="example2.com", name="example2")
        Site.objects.create(id=3, domain="example3.com", name="example3")

        # attempt to delete sites
        data = {
            "action": "delete_selected",
            "_selected_action": [site.pk for site in Site.objects.all()],
        }
        response = self.app.post(
            reverse("admin:sites_site_changelist"), data, user=self.user
        ).follow()

        # check sites
        sites = Site.objects.all()
        self.assertEqual(len(sites), 3)

        # check message
        doc = PyQuery(response.content)

        warning_msg = doc.find(".warning").text()
        self.assertEqual(
            warning_msg,
            _("You cannot delete all websites; at least one site must remain."),
        )


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
