from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

from playwright.sync_api import expect

from ...cms.tests import cms_tools
from ...utils.tests.playwright import PlaywrightSyncLiveServerTestCase
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


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CookieBannerPlaywrightTests(PlaywrightSyncLiveServerTestCase):
    def setUp(self):
        from open_inwoner.accounts.tests.factories import DigidUserFactory

        super().setUp()

        self.user = DigidUserFactory.create()
        self.user_login_state = self.get_user_bsn_login_state(self.user)

    def test_cookie_accept(self):
        config = SiteConfiguration.get_solo()

        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()
        page.goto(self.live_reverse("profile:action_list"))

        expect(page.get_by_text(config.cookie_info_text)).to_be_visible()

        accept_button = page.get_by_text(_("Alles toestaan"))
        accept_button.click()

        cookie_banner_accepted = None
        for cookie in page.context.cookies():
            if cookie["name"] == "cookieBannerAccepted" and cookie["value"] == "true":
                cookie_banner_accepted = True

        self.assertTrue(cookie_banner_accepted)
        expect(page.get_by_text(config.cookie_info_text)).to_be_hidden()

    def test_cookie_reject(self):
        config = SiteConfiguration.get_solo()

        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()
        page.goto(self.live_reverse("profile:action_list"))

        expect(page.get_by_text(config.cookie_info_text)).to_be_visible()

        reject_button = page.get_by_text(_("Alles weigeren"))
        reject_button.click()

        cookie_banner_accepted = None
        for cookie in page.context.cookies():
            if cookie["name"] == "cookieBannerAccepted" and cookie["value"] == "false":
                cookie_banner_accepted = False

        self.assertFalse(cookie_banner_accepted)
        expect(page.get_by_text(config.cookie_info_text)).to_be_hidden()
