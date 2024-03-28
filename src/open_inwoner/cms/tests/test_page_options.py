from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from django_webtest import WebTest
from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.ssd.cms_apps import SSDApphook

from ..cases.cms_apps import CasesApphook
from ..collaborate.cms_apps import CollaborateApphook
from ..inbox.cms_apps import InboxApphook
from ..products.cms_apps import ProductsApphook
from ..profile.cms_apps import ProfileApphook
from ..tests import cms_tools


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestCMSHelpText(TestCase):
    """
    Test cases for CMS page-specific help texts

    See /open_inwoner/configurations/tests/test_help_modal.py for
    global help texts defined via SiteConfiguration.
    """

    def setUp(self):
        self.user = UserFactory()
        self.user.set_password("12345")
        self.user.email = "test@email.com"
        self.user.save()

    @patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
    def test_home_page_help_text(self, mock_solo):
        mock_solo.return_value.cookiebanner_enabled = False

        cms_tools.create_homepage(
            extension_args={
                "help_text": "Help! I need somebody. Help!",
            },
        )

        url = reverse("pages-root")
        self.client.login(email=self.user.email, password="12345")
        response = self.client.get(url)

        doc = PyQuery(response.content.decode("utf-8"))

        modal = doc.find(".help-modal")[0]
        self.assertEqual(modal.attrib["data-help-text"], "Help! I need somebody. Help!")

    @patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
    def test_apphook_page_help_text(self, mock_solo):
        mock_solo.return_value.cookiebanner_enabled = False

        test_cases = [
            (CollaborateApphook, "collaborate:plan_list"),
            (InboxApphook, "inbox:index"),
            (ProductsApphook, "products:category_list"),
            (ProfileApphook, "profile:detail"),
            (SSDApphook, "ssd:uitkeringen"),
        ]
        for i, (cms_apphook, url_name) in enumerate(test_cases):
            with self.subTest(f"Test help text for {cms_apphook} page"):
                cms_tools.create_apphook_page(
                    cms_apphook,
                    extension_args={
                        "help_text": "Help! I need somebody. Help!",
                    },
                )

                url = reverse(url_name)
                self.client.login(email=self.user.email, password="12345")
                response = self.client.get(url)

                doc = PyQuery(response.content.decode("utf-8"))

                modal = doc.find(".help-modal")[0]
                self.assertEqual(
                    modal.attrib["data-help-text"], "Help! I need somebody. Help!"
                )
