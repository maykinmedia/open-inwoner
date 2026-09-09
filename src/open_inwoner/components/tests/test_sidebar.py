from django.test import override_settings
from django.urls import reverse

from cms import api
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests.cms_tools import (
    create_apphook_page,
    create_homepage,
    publish_page,
)


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
