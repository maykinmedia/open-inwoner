from django.urls import reverse

from django_webtest import WebTest

from ..models import SiteConfiguration


class TestRenderedAnalytics(WebTest):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()

    def test_google_html_code_exists_in_home_page_when_it_is_configured(self):
        self.config.gtm_code = "GTM-XXXX"
        self.config.ga_code = "G-XXXXX"
        self.config.save()
        response = self.app.get(reverse("root"))

        self.assertTemplateUsed(response, "analytics/google.html")
        self.assertContains(response, "<!-- Google Tag Manager -->")
        self.assertContains(
            response, "<!-- Global site tag (gtag.js) - Google Analytics -->"
        )

    def test_google_html_code_does_not_exist_in_home_page_when_it_is_not_configured(
        self,
    ):
        response = self.app.get(reverse("root"))

        self.assertTemplateUsed(response, "analytics/google.html")
        self.assertNotContains(response, "<!-- Google Tag Manager -->")
        self.assertNotContains(
            response, "<!-- Global site tag (gtag.js) - Google Analytics -->"
        )

    def test_matomo_html_code_exists_in_home_page_when_it_is_configured(self):
        self.config.matomo_url = "example.com"
        self.config.matomo_site_id = "1"
        self.config.save()
        response = self.app.get(reverse("root"))

        self.assertTemplateUsed(response, "analytics/matomo.html")
        self.assertContains(response, "<!-- Matomo -->")

    def test_matomo_html_code_does_not_exist_in_home_page_when_it_is_not_configured(
        self,
    ):
        response = self.app.get(reverse("root"))

        self.assertTemplateUsed(response, "analytics/matomo.html")
        self.assertNotContains(response, "<!-- Matomo -->")
