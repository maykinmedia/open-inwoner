from django.urls import reverse

from cms.utils.permissions import set_current_user
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.extensions.constants import Icons


@disable_admin_mfa()
class MenuIconsAdminViewTests(WebTest):
    def setUp(self):
        set_current_user(
            None
        )  # otherwise will assume previous user is logged in (who is often deleted after test)
        return super().setUp()

    def test_get_menu_icons(self):
        user = UserFactory(is_staff=True, is_superuser=True)
        url = reverse("admin:cms_extensions_menu_icons")

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)
        for value, label in Icons.choices:
            self.assertContains(response, value)
            self.assertContains(response, label)

    def test_menu_icon_help_text_links_to_menu_icons_page(self):
        user = UserFactory(is_staff=True, is_superuser=True)
        url = reverse("admin:extensions_commonextension_add")

        response = self.app.get(url, user=user)

        self.assertContains(response, reverse("admin:cms_extensions_menu_icons"))
