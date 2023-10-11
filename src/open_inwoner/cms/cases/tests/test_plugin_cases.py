from unittest.mock import patch

from django.test import TestCase, override_settings

import requests_mock

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

    def test_cms_plugin_cases_are_rendered(self, m):
        self._setUpMocks(m)

        html, context = cms_tools.render_plugin(CasesPlugin, user=self.user)

        cases = context["cases"]

        self.assertEqual(len(cases), 2)

        self.assertEqual(cases[0].omschrijving, "Coffee zaak 1")
        self.assertEqual(cases[1].omschrijving, "Coffee zaak 2")
