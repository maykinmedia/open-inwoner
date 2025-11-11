from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from pyquery import PyQuery

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.plugins.cms_plugins import CMSZakenPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.tests.factories import (
    ServiceFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.shared import ZAKEN_ROOT


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSZakenPluginTest(TestCase):
    def setUp(self):
        self.user = UserFactory(login_type=LoginTypeChoices.digid, bsn="123456789")

    def test_plugin_renders_htmx_loading_placeholder(self):
        """
        Test that plugin initially renders a loading spinner with HTMX attributes
        """
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=self.user,
        )

        pyquery = PyQuery(html)

        self.assertIn("Mijn Zaken", html)

        spinner = pyquery.find(".spinner")
        self.assertEqual(len(spinner), 1)
        self.assertIn("Zaken laden...", html)

        # Check that HTMX attributes are present on the container div
        htmx_container = pyquery.find("[hx-get]")
        self.assertEqual(
            len(htmx_container), 1, "Should have exactly one element with hx-get"
        )
        self.assertEqual(htmx_container.attr("hx-trigger"), "load")
        self.assertEqual(htmx_container.attr("hx-swap"), "innerHTML")
        # Check that the HTMX container has the correct ID pattern
        self.assertTrue(htmx_container.attr("id").startswith("zaken-content-"))

        # Check that hx-get URL is constructed correctly
        hxget = context["hxget"]
        self.assertIn("/cms-plugins/zaken/", hxget)
        self.assertIn("/content/", hxget)

    def test_plugin_does_not_render_for_unauthenticated_user(self):
        """Test that the plugin doesn't render for users without appropriate login type"""
        user = UserFactory(login_type=LoginTypeChoices.default)
        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=user,
        )

        self.assertNotIn("hxget", context)
        # Should not render the plugin content
        self.assertEqual(html.strip(), "")

    def test_plugin_does_not_render_without_zgw_api_group_config(self):
        ZGWApiGroupConfig.objects.all().delete()

        user = UserFactory(login_type=LoginTypeChoices.digid)
        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=user,
        )

        # Should not have the hxget in context
        self.assertNotIn("hxget", context)
        # Should not render the plugin content
        self.assertEqual(html.strip(), "")

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
        return_value=[],
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_htmx_content_endpoint_returns_empty_state(
        self, mock_submissions, mock_cases
    ):
        """
        Test that the HTMX endpoint returns empty state when no cases exist
        """
        ServiceFactory(api_root=ZAKEN_ROOT)
        ZGWApiGroupConfigFactory()
        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(
            url,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn("Geen zaken gevonden", content)

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_htmx_content_endpoint_returns_cases(self, mock_submissions, mock_cases):
        """
        Test that the HTMX endpoint returns case data
        """
        api_group = ZGWApiGroupConfigFactory()
        mock_case = MagicMock()
        mock_case.process_data.return_value = {
            "uuid": "test-uuid-123",
            "identification": "ZAAK-001",
            "description": "Test zaak beschrijving",
            "current_status": "In behandeling",
            "case_type": "Test zaaktype",
            "api_group": api_group,
        }
        mock_cases.return_value = [mock_case]
        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(
            url,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        pyquery = PyQuery(content)
        cards = pyquery.find(".card")
        self.assertEqual(len(cards), 1)

        self.assertIn("In behandeling", content)
        self.assertIn("Test zaak beschrijving", content)
        self.assertIn("ZAAK-001", content)

    def test_htmx_content_endpoint_requires_htmx(self):
        """
        Test that the content endpoint requires HTMX header
        """
        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url)

        # Should return 400 Bad Request without HTMX header
        self.assertEqual(response.status_code, 400)
