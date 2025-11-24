from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from pyquery import PyQuery

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.plugins.cms_plugins import CMSZakenPlugin
from open_inwoner.cms.plugins.models.zaken import MAX_CASES_DEFAULT
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

    def test_plugin_does_not_render_for_anonymous_user(self):
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=None,
        )

        self.assertNotIn("hxget", context)
        self.assertEqual(html.strip(), "")

    def test_plugin_does_not_render_for_user_with_wrong_login_type(self):
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

    @patch("open_inwoner.cms.plugins.views.CaseListService")
    def test_htmx_content_endpoint_returns_empty_without_zgw_api_group_config(
        self, mock_case_list_service
    ):
        """
        Test that the HTMX content endpoint returns early when no ZGWApiGroupConfig exists
        """
        ZGWApiGroupConfig.objects.all().delete()

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

        self.assertIn("U heeft op dit moment geen lopende zaken.", content)

        # CaseListService should not be instantiated, we return early
        mock_case_list_service.assert_not_called()

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
        self.assertIn("U heeft op dit moment geen lopende zaken.", content)

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

    def test_plugin_includes_num_zaken_in_hxget_url(self):
        """
        Test that the plugin includes num_zaken parameter in the HTMX URL
        """
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken", "num_zaken": 5},
            user=self.user,
        )

        # Check that hx-get URL contains num_zaken parameter
        hxget = context["hxget"]
        self.assertIn("num_zaken=5", hxget)

    def test_plugin_uses_default_num_zaken_value(self):
        """
        Test that the plugin uses the default num_zaken value (4) when not specified
        """
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=self.user,
        )

        # Check that hx-get URL contains default num_zaken parameter
        hxget = context["hxget"]
        self.assertIn("num_zaken=4", hxget)

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_num_zaken_parameter_limits_results(self, mock_submissions, mock_cases):
        """
        Test that the num_zaken query parameter correctly limits the number of returned cases
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_cases_list = []
        for i in range(10):
            mock_case = MagicMock()
            mock_case.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "description": f"Test zaak {i}",
                "current_status": "In behandeling",
                "case_type": "Test zaaktype",
                "api_group": api_group,
            }
            mock_cases_list.append(mock_case)

        mock_cases.return_value = mock_cases_list

        plugin_model = cms_tools._init_plugin(
            CMSZakenPlugin, {"title": "Mijn Zaken", "num_zaken": 3}
        )

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(
            url,
            {"num_zaken": "3"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        pyquery = PyQuery(content)
        cards = pyquery.find(".card")

        self.assertEqual(len(cards), 3)

        # Verify it shows the first 3 cases
        self.assertIn("ZAAK-000", content)
        self.assertIn("ZAAK-001", content)
        self.assertIn("ZAAK-002", content)
        self.assertNotIn("ZAAK-003", content)

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_num_zaken_parameter_with_different_values(
        self, mock_submissions, mock_cases
    ):
        """
        Test that different num_zaken values return correct number of cases
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_cases_list = []
        for i in range(10):
            mock_case = MagicMock()
            mock_case.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "description": f"Test zaak {i}",
                "current_status": "In behandeling",
                "case_type": "Test zaaktype",
                "api_group": api_group,
            }
            mock_cases_list.append(mock_case)

        mock_cases.return_value = mock_cases_list

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        test_cases = ["2", "7", "10"]
        for num_zaken in test_cases:
            with self.subTest(num_zaken=num_zaken):
                response = self.client.get(
                    url,
                    {"num_zaken": num_zaken},
                    HTTP_HX_REQUEST="true",
                )
                pyquery = PyQuery(response.content.decode("utf-8"))
                self.assertEqual(len(pyquery.find(".card")), int(num_zaken))

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
    )
    def test_num_zaken_parameter_with_mixed_submissions_and_cases(
        self, mock_submissions, mock_cases
    ):
        """
        Test that num_zaken correctly limits combined submissions and cases
        """
        api_group = ZGWApiGroupConfigFactory()

        # 3 mock submissions
        mock_submissions_list = []
        for i in range(3):
            mock_submission = MagicMock()
            mock_submission.process_data.return_value = {
                "uuid": f"submission-uuid-{i}",
                "identification": f"SUBMISSION-{i:03d}",
                "description": f"Test submission {i}",
                "current_status": "Open",
                "case_type": "Submission type",
                "api_group": api_group,
            }
            mock_submissions_list.append(mock_submission)

        # 7 mock cases
        mock_cases_list = []
        for i in range(7):
            mock_case = MagicMock()
            mock_case.process_data.return_value = {
                "uuid": f"case-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "description": f"Test zaak {i}",
                "current_status": "In behandeling",
                "case_type": "Test zaaktype",
                "api_group": api_group,
            }
            mock_cases_list.append(mock_case)

        mock_submissions.return_value = mock_submissions_list
        mock_cases.return_value = mock_cases_list

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        # Test with num_zaken=5 (should get 3 submissions + 2 cases)
        response = self.client.get(
            url,
            {"num_zaken": "5"},
            HTTP_HX_REQUEST="true",
        )
        content = response.content.decode("utf-8")
        pyquery = PyQuery(content)

        self.assertEqual(len(pyquery.find(".card")), 5)

        # Verify submissions come first
        self.assertIn("SUBMISSION-000", content)
        self.assertIn("SUBMISSION-001", content)
        self.assertIn("SUBMISSION-002", content)
        # Then cases
        self.assertIn("ZAAK-000", content)
        self.assertIn("ZAAK-001", content)
        # But not the 3rd case
        self.assertNotIn("ZAAK-002", content)

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_num_zaken_parameter_handles_invalid_string(
        self, mock_submissions, mock_cases
    ):
        """
        Test that invalid string values for num_zaken fall back to MAX_CASES_DEFAULT
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_cases_list = []
        for i in range(15):
            mock_case = MagicMock()
            mock_case.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "description": f"Test zaak {i}",
                "current_status": "In behandeling",
                "case_type": "Test zaaktype",
                "api_group": api_group,
            }
            mock_cases_list.append(mock_case)

        mock_cases.return_value = mock_cases_list

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        # Test with invalid string - should fall back to MAX_CASES_DEFAULT
        response = self.client.get(
            url,
            {"num_zaken": "invalid"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)

        pyquery = PyQuery(response.content.decode("utf-8"))
        cards = pyquery.find(".card")
        # Should return MAX_CASES_DEFAULT instead of crashing
        self.assertEqual(len(cards), MAX_CASES_DEFAULT)

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_num_zaken_parameter_handles_negative_value(
        self, mock_submissions, mock_cases
    ):
        """
        Test that negative values for num_zaken fall back to MAX_CASES_DEFAULT
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_cases_list = []
        for i in range(15):
            mock_case = MagicMock()
            mock_case.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "description": f"Test zaak {i}",
                "current_status": "In behandeling",
                "case_type": "Test zaaktype",
                "api_group": api_group,
            }
            mock_cases_list.append(mock_case)

        mock_cases.return_value = mock_cases_list

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        # Test with negative value - should fall back to MAX_CASES_DEFAULT
        response = self.client.get(
            url,
            {"num_zaken": "-5"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)

        pyquery = PyQuery(response.content.decode("utf-8"))
        cards = pyquery.find(".card")
        # Should return MAX_CASES_DEFAULT instead of processing negative value
        self.assertEqual(len(cards), MAX_CASES_DEFAULT)

    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_cases",
    )
    @patch(
        "open_inwoner.cms.plugins.views.CaseListService.get_submissions",
        return_value=[],
    )
    def test_num_zaken_parameter_handles_excessive_value(
        self, mock_submissions, mock_cases
    ):
        """
        Test that values over MAX_CASES_DEFAULT fall back to MAX_CASES_DEFAULT
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_cases_list = []
        for i in range(15):
            mock_case = MagicMock()
            mock_case.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "description": f"Test zaak {i}",
                "current_status": "In behandeling",
                "case_type": "Test zaaktype",
                "api_group": api_group,
            }
            mock_cases_list.append(mock_case)

        mock_cases.return_value = mock_cases_list

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        # Test with excessive value - should fall back to MAX_CASES_DEFAULT
        response = self.client.get(
            url,
            {"num_zaken": "20"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)

        pyquery = PyQuery(response.content.decode("utf-8"))
        cards = pyquery.find(".card")
        # Should return MAX_CASES_DEFAULT
        self.assertEqual(len(cards), MAX_CASES_DEFAULT)
