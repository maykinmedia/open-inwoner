from django.test import TestCase
from django.urls import reverse

from ...cms.tests import cms_tools
from ..models import SiteConfiguration


class TestRenderedAnalytics(TestCase):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()
        cms_tools.create_homepage()
        self.client.cookies["cookieBannerAccepted"] = "true"

    def test_google_html_code_exists_in_home_page_when_it_is_configured(self):
        self.config.gtm_code = "GTM-XXXX"
        self.config.ga_code = "G-XXXXX"
        self.config.save()
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "analytics/google.html")
        self.assertContains(response, "<!-- Google Tag Manager -->")
        self.assertContains(
            response, "<!-- Global site tag (gtag.js) - Google Analytics -->"
        )

    def test_google_html_code_does_not_exist_in_home_page_when_it_is_not_configured(
        self,
    ):
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "analytics/google.html")
        self.assertNotContains(response, "<!-- Google Tag Manager -->")
        self.assertNotContains(
            response, "<!-- Global site tag (gtag.js) - Google Analytics -->"
        )

    def test_matomo_html_code_exists_in_home_page_when_it_is_configured(self):
        self.config.matomo_url = "example.com"
        self.config.matomo_site_id = "1"
        self.config.save()
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "analytics/matomo.html")
        self.assertContains(response, "<!-- Matomo -->")

    def test_matomo_html_code_does_not_exist_in_home_page_when_it_is_not_configured(
        self,
    ):
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "analytics/matomo.html")
        self.assertNotContains(response, "<!-- Matomo -->")

    def test_siteimprove_html_code_exists_in_home_page_when_it_is_configured(self):
        self.config.siteimprove_id = "555"
        self.config.save()
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "analytics/siteimprove.html")
        self.assertContains(response, "<!-- SiteImprove -->")

    def test_siteimprove_html_code_does_not_exist_in_home_page_when_it_is_not_configured(
        self,
    ):
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "analytics/siteimprove.html")
        self.assertNotContains(response, "<!-- SiteImprove -->")


class TestCookieBannerDisabled(TestCase):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()
        cms_tools.create_homepage()
        self.config.cookie_info_text = ""
        self.config.save()

    def test_cookiebanner_code_does_not_exist_in_home_page_when_it_is_not_configured(
        self,
    ):
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateUsed(response, "master.html")
        self.assertNotContains(response, "<!-- cookiebanner -->")

    def test_google_analytics_not_rendered(self):
        self.config.gtm_code = "GTM-XXXX"
        self.config.ga_code = "G-XXXXX"
        self.config.save()
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateNotUsed(response, "analytics/google.html")
        self.assertNotContains(response, "<!-- Google Tag Manager -->")
        self.assertNotContains(
            response, "<!-- Global site tag (gtag.js) - Google Analytics -->"
        )

    def test_matomo_analytics_not_rendered(self):
        self.config.matomo_url = "example.com"
        self.config.matomo_site_id = "1"
        self.config.save()
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateNotUsed(response, "analytics/matomo.html")
        self.assertNotContains(response, "<!-- Matomo -->")

    def test_siteimprove_analytics_not_rendered(self):
        self.config.siteimprove_id = "555"
        self.config.save()
        response = self.client.get(reverse("pages-root"))

        self.assertTemplateNotUsed(response, "analytics/siteimprove.html")
        self.assertNotContains(response, "<!-- SiteImprove -->")
