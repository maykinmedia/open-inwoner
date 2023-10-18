from unittest.mock import patch

from django.test import TestCase, override_settings

import lxml
import requests_mock
from pyquery import PyQuery as pq

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.tests.mixins import ZakenTestMixin
from open_inwoner.utils.test import ClearCachesMixin

from ...tests import cms_tools
from ..cms_apps import CasesApphook
from ..cms_plugins import CasesPlugin


@requests_mock.Mocker()
@patch.object(CasesPlugin, "limit", 2)
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CasesPluginTest(ZakenTestMixin, ClearCachesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cms_tools.create_apphook_page(CasesApphook)

    def test_cms_plugin_cases_not_rendered_for_anonymous_user(self, m):
        self.setUpMocks(m)

        # anonymous user
        html, context = cms_tools.render_plugin(CasesPlugin)

        self.assertIsNone(context["cases"])

        # check that html empty
        with self.assertRaises(lxml.etree.ParserError) as ctx:
            pq(html)

        self.assertEqual(str(ctx.exception), "Document is empty")

    def test_cms_plugin_cases_not_rendered_for_non_digid_user(self, m):
        self.setUpMocks(m)

        user = UserFactory()
        user.login_type = LoginTypeChoices.default
        user.save()

        html, context = cms_tools.render_plugin(CasesPlugin, user=user)

        self.assertIsNone(context["cases"])

        # check that html empty
        with self.assertRaises(lxml.etree.ParserError) as ctx:
            pq(html)

        self.assertEqual(str(ctx.exception), "Document is empty")

    def test_cms_plugin_cases_rendered(self, m):
        self.setUpMocks(m)
        self.setUpMocksExtra(m)  # create additional zaken

        # the ZakenTestMixin user is a digid user
        html, context = cms_tools.render_plugin(CasesPlugin, user=self.user)

        cases = context["cases"]

        # check that limiting display works (ZakenTestMixin creates 3 zaken)
        self.assertEqual(len(cases), 2)

        self.assertEqual(cases[0].omschrijving, "Coffee zaak 1")
        self.assertEqual(cases[1].omschrijving, "Coffee zaak 2")

        # check html
        doc = pq(html)

        case_descriptions = doc.find(".h4").find("span")

        for case_description, case in zip(case_descriptions, cases):
            self.assertEqual(case_description.text, case.omschrijving)

        case_link_paths = (case.url.rsplit("/", 1)[-1] for case in cases)
        html_case_links = doc.find("a")

        for html_link, path in zip(html_case_links, case_link_paths):
            self.assertEqual(html_link.attrib["href"], f"/cases/{path}/status/")
