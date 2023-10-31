from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from pyquery import PyQuery as pq

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.tests.mixins import ZakenTestMixin
from open_inwoner.utils.test import ClearCachesMixin

from ...tests import cms_tools
from ...tests.cms_tools import get_request
from ..cms_apps import CasesApphook
from ..cms_plugins import CasesPlugin


def render_htmx_plugin(plugin_class, *, user=None) -> tuple[str, dict]:
    # this could be moved to cmstools when re-used
    request = get_request(user=user, htmx=True)
    context = plugin_class.render_content(request)
    html = render_to_string(plugin_class.render_template, context, request=request)
    html = html.strip()
    return html, context


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

        self.assertIsNone(context)
        self.assertEqual(html, "")

    def test_cms_plugin_cases_not_rendered_for_non_digid_user(self, m):
        self.setUpMocks(m)

        user = UserFactory()
        user.login_type = LoginTypeChoices.default
        user.save()

        html, context = cms_tools.render_plugin(CasesPlugin, user=user)

        self.assertIsNone(context)
        self.assertEqual(html, "")

    def test_cms_plugin_renders_htmx_trigger(self, m):
        self.setUpMocks(m)
        html, context = cms_tools.render_plugin(CasesPlugin, user=self.user)

        self.assertEqual(context["hxget"], reverse("cases:cases_plugin_content"))

        doc = pq(html)
        trigger = doc.find("#spinner")
        self.assertEqual(trigger.attr["hx-get"], reverse("cases:cases_plugin_content"))
        self.assertEqual(trigger.attr["hx-trigger"], "load")

    def test_cms_plugin_view_renders_cases(self, m):
        self.setUpMocks(m)
        self.setUpMocksExtra(m)

        html, context = render_htmx_plugin(CasesPlugin, user=self.user)

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
            # TODO reverse
            self.assertEqual(html_link.attrib["href"], rf"/cases/{path}/status/")

    def test_cms_plugin_view_requires_digid_and_htmx(self, m):
        self.setUpMocks(m)
        self.setUpMocksExtra(m)

        url = reverse("cases:cases_plugin_content")

        with self.subTest("anonymous"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400)

        with self.subTest("not bsn"):
            user = UserFactory()
            user.login_type = LoginTypeChoices.default
            user.save()
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400)

        with self.subTest("digid"):
            self.client.force_login(self.user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 400)

        with self.subTest("digid and htmx"):
            self.client.force_login(self.user)
            response = self.client.get(url, HTTP_HX_REQUEST="true")
            self.assertEqual(response.status_code, 200)
