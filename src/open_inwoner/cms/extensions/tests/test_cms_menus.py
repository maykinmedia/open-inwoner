from django.test import TestCase

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.tests.cms_tools import create_apphook_page, create_homepage


class MenuModifierVisibilityTests(TestCase):
    def setUp(self):
        homepage = create_homepage()
        page = create_apphook_page(
            CasesApphook,
            parent_page=homepage,
            extension_args={"requires_auth_bsn_or_kvk": True},
        )
        self.cases_url = page.get_absolute_url()

    def _menu_hrefs(self, user=None):
        if user:
            self.client.force_login(user)
        response = self.client.get("/")
        doc = PyQuery(response.content)
        return [
            a.attrib.get("href") for a in doc.find(".primary-navigation__list-item a")
        ]

    def test_bsn_or_kvk_page_hidden_for_user_without_bsn_or_kvk(self):
        user = UserFactory(bsn="", kvk="")

        self.assertNotIn(self.cases_url, self._menu_hrefs(user))

    def test_bsn_or_kvk_page_hidden_for_anonymous_user(self):
        self.assertNotIn(self.cases_url, self._menu_hrefs())

    def test_bsn_or_kvk_page_shown_for_digid_user(self):
        self.assertIn(self.cases_url, self._menu_hrefs(DigidUserFactory()))

    def test_bsn_or_kvk_page_shown_for_staff_user_without_bsn_or_kvk(self):
        user = UserFactory(bsn="", kvk="", is_staff=True)

        self.assertIn(self.cases_url, self._menu_hrefs(user))
