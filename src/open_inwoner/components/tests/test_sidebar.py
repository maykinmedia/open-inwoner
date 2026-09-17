from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from cms import api
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory, eHerkenningUserFactory
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests.cms_tools import (
    create_apphook_page,
    create_homepage,
    publish_page,
)
from open_inwoner.kvk.tests.factories import CertificateFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SidebarContentTests(WebTest):
    """The sidenav replaces page-specific sidebar content wherever it renders."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.home_page = create_homepage()

        ProfileConfig.objects.create(namespace=ProfileApphook.app_name)
        create_apphook_page(ProfileApphook, parent_page=self.home_page)

    def test_sidenav_replaces_anchor_menu_for_authenticated_user(self):
        page = api.create_page(
            "Samenwerken",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
            slug="samenwerken",
        )
        publish_page(page, "nl")

        response = self.app.get(reverse("profile:detail"), user=self.user)

        sidebar = response.pyquery(".grid__sidebar")
        self.assertTrue(sidebar.find(".side-navigation--oip"))
        self.assertFalse(sidebar.find(".anchor-menu--desktop"))

    def test_anchor_menu_is_kept_when_there_are_no_sidenav_items(self):
        # the profile page itself is excluded from the sidenav, so without other
        # pages below the homepage there is nothing to show
        response = self.app.get(reverse("profile:detail"), user=self.user)

        sidebar = response.pyquery(".grid__sidebar")
        self.assertFalse(sidebar.find(".side-navigation--oip"))
        self.assertTrue(sidebar.find(".anchor-menu--desktop"))


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class SidenavHiddenTest(WebTest):
    """The sidenav must stay hidden on views outside normal navigation"""

    def setUp(self):
        super().setUp()
        self.home_page = create_homepage()

        # a page under the homepage that should be hidden
        page = api.create_page(
            "Samenwerken",
            "cms/fullwidth.html",
            "nl",
            parent=self.home_page,
            in_navigation=True,
            slug="samenwerken",
        )
        publish_page(page, "nl")

    def _assert_sidenav_hidden(self, response):
        sidebar = response.pyquery(".grid__sidebar")
        self.assertFalse(sidebar.find(".side-navigation--oip"))

    def test_sidenav_hidden_on_kvk_branch_selection(self):
        user = eHerkenningUserFactory(kvk="12345678")

        with (
            patch(
                "open_inwoner.kvk.client.KvKClient.get_all_company_branches",
                return_value=[
                    {
                        "kvkNummer": "12345678",
                        "vestigingsnummer": "1234",
                        "naam": "Acme",
                    }
                ],
            ),
            patch(
                "open_inwoner.kvk.client.KvKClient.get_basisprofiel", return_value={}
            ),
            patch("open_inwoner.kvk.models.KvKConfig.get_solo") as mock_solo,
        ):
            mock_solo.return_value.api_key = "123"
            mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
            mock_solo.return_value.client_certificate = CertificateFactory()
            mock_solo.return_value.server_certificate = CertificateFactory()

            response = self.app.get(reverse("kvk:branches"), user=user)

        self._assert_sidenav_hidden(response)

    def test_sidenav_hidden_on_registration_necessary(self):
        user = UserFactory()

        response = self.app.get(reverse("profile:registration_necessary"), user=user)

        self._assert_sidenav_hidden(response)

    def test_sidenav_hidden_on_email_verification(self):
        user = UserFactory(email="foo@example.com")

        response = self.app.get(reverse("profile:email_verification_user"), user=user)

        self._assert_sidenav_hidden(response)
