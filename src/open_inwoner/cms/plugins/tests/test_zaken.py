from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from django.urls import reverse

from pyquery import PyQuery

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.plugins.cms_plugins import CMSZakenPlugin
from open_inwoner.cms.plugins.models.zaken import MAX_CASES_DEFAULT
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.services import ZakenResult
from open_inwoner.openzaak.tests.factories import (
    ServiceFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.openzaak.tests.shared import ZAKEN_ROOT


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSZakenPluginTest(TestCase):
    def setUp(self):
        self.user = UserFactory(login_type=LoginTypeChoices.digid, bsn="123456789")

    def test_plugin_renders_for_authenticated_bsn_user(self):
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken", "num_zaken": 4},
            user=self.user,
        )

        # Check that context has the expected keys
        self.assertIn("show_zaken_plugin", context)
        self.assertIn("plugin_title", context)
        self.assertIn("mijn_zaken_url", context)
        self.assertIn("hx_get_url", context)

        # Verify values
        self.assertEqual(context["plugin_title"], "Mijn Zaken")
        self.assertIn("/cases/", context["mijn_zaken_url"])
        self.assertIn("/cms-plugins/zaken/", context["hx_get_url"])
        self.assertIn("/content/", context["hx_get_url"])
        self.assertIn("num_zaken=4", context["hx_get_url"])

        # Check that web component container is rendered
        self.assertIn("oip-home-plugin-section", html)
        self.assertIn("Mijn Zaken", html)
        self.assertIn("hx-get", html)

    def test_plugin_does_not_render_without_zgw_api_group_config(self):
        ZGWApiGroupConfig.objects.all().delete()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=self.user,
        )

        # Should not have plugin-specific context keys
        self.assertNotIn("plugin_title", context)
        self.assertNotIn("hx_get_url", context)
        self.assertNotIn("show_zaken_plugin", context)

        # Should not contain any actual plugin content
        self.assertNotIn("oip-home-plugin-section", html)
        self.assertNotIn("oip-home-plugin-card", html)

    def test_plugin_does_not_render_for_anonymous_user(self):
        ZGWApiGroupConfigFactory()
        anonymous_user = AnonymousUser()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=anonymous_user,
        )

        self.assertNotIn("plugin_title", context)
        self.assertNotIn("hx_get_url", context)

    def test_plugin_does_not_render_for_non_bsn_user(self):
        ZGWApiGroupConfigFactory()
        non_bsn_user = UserFactory(login_type=LoginTypeChoices.default, bsn="")

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=non_bsn_user,
        )

        self.assertNotIn("plugin_title", context)
        self.assertNotIn("hx_get_url", context)

    def test_plugin_uses_default_num_zaken_value(self):
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken"},
            user=self.user,
        )

        # Default is 4 based on the model default
        hx_get_url = context["hx_get_url"]
        self.assertIn("num_zaken=4", hx_get_url)

    def test_plugin_includes_custom_num_zaken_in_url(self):
        ZGWApiGroupConfigFactory()

        html, context = cms_tools.render_plugin(
            CMSZakenPlugin,
            plugin_data={"title": "Mijn Zaken", "num_zaken": 7},
            user=self.user,
        )

        hx_get_url = context["hx_get_url"]
        self.assertIn("num_zaken=7", hx_get_url)

    def test_htmx_content_endpoint_requires_htmx(self):
        ZGWApiGroupConfigFactory()
        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url)  # No HTMX header

        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)

    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken",
        return_value=ZakenResult(zaken=[], skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    def test_htmx_content_endpoint_returns_empty_state(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        ServiceFactory(api_root=ZAKEN_ROOT)
        ZGWApiGroupConfigFactory()
        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Should have no zaak items
        self.assertNotIn("oip-home-plugin-card", content)

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    def test_htmx_content_endpoint_returns_cases(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_zaak = MagicMock()
        mock_zaak.process_data.return_value = {
            "uuid": "test-uuid-123",
            "identification": "ZAAK-001",
            "naam": "Test zaak beschrijving",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }
        mock_visible_zaken.return_value = ZakenResult(zaken=[mock_zaak], skipped=[])

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Should render zaak items
        pyquery = PyQuery(content)
        zaak_items = pyquery.find("oip-home-plugin-card")
        self.assertEqual(len(zaak_items), 1)

        # Check attributes (note: template uses 'identificatie' not 'identification')
        zaak_item = zaak_items.eq(0)
        self.assertEqual(zaak_item.attr("identificatie"), "ZAAK-001")
        self.assertIn("Zaaknummer", zaak_item.attr("description"))
        self.assertIn("ZAAK-001", zaak_item.attr("description"))
        self.assertIn("test-uuid-123", zaak_item.attr("detail-url"))

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_formulieren")
    def test_htmx_content_endpoint_complete_failure(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        mock_visible_zaken.side_effect = Exception("Cases API error")
        mock_formulieren.side_effect = Exception("formulieren API error")

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Should have no zaak items
        self.assertNotIn("oip-home-plugin-card", content)

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_formulieren")
    def test_htmx_content_endpoint_partial_failure(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        # formulieren fail
        mock_formulieren.side_effect = Exception("Formulieren API error")

        # Cases succeed
        mock_zaak = MagicMock()
        mock_zaak.process_data.return_value = {
            "uuid": "test-uuid-123",
            "identification": "ZAAK-001",
            "naam": "Test zaak",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }
        mock_visible_zaken.return_value = ZakenResult(zaken=[mock_zaak], skipped=[])

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Should render cases that were retrieved
        pyquery = PyQuery(content)
        zaak_items = pyquery.find("oip-home-plugin-card")
        self.assertEqual(len(zaak_items), 1)

        # Should have error message in slot
        error_slot = pyquery.find('[slot="error"]')
        self.assertEqual(len(error_slot), 1)
        self.assertIn("technisch probleem", error_slot.text().lower())

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    def test_num_zaken_parameter_limits_results(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_cases_list = []
        for i in range(10):
            mock_zaak = MagicMock()
            mock_zaak.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "naam": f"Test zaak {i}",
                "api_group": api_group,
                "type_aanvraag": TypeAanvraag.ZAAK.value,
            }
            mock_cases_list.append(mock_zaak)

        mock_visible_zaken.return_value = ZakenResult(zaken=mock_cases_list, skipped=[])

        plugin_model = cms_tools._init_plugin(
            CMSZakenPlugin, {"title": "Mijn Zaken", "num_zaken": 3}
        )

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, {"num_zaken": "3"}, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        pyquery = PyQuery(content)
        zaak_items = pyquery.find("oip-home-plugin-card")

        # Should only return 3 items
        self.assertEqual(len(zaak_items), 3)

        # Verify it shows the first 3 cases
        identifications = [pyquery(item).attr("identificatie") for item in zaak_items]
        self.assertIn("ZAAK-000", identifications)
        self.assertIn("ZAAK-001", identifications)
        self.assertIn("ZAAK-002", identifications)

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_formulieren")
    def test_num_zaken_parameter_with_mixed_formulieren_and_cases(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        # 3 mock formulieren
        mock_formulieren_list = []
        for i in range(3):
            mock_submission = MagicMock()
            mock_submission.process_data.return_value = {
                "uuid": f"submission-uuid-{i}",
                "identification": f"SUBMISSION-{i:03d}",
                "naam": f"Test submission {i}",
                "api_group": api_group,
                "type_aanvraag": TypeAanvraag.FORMULIER.value,
            }
            mock_formulieren_list.append(mock_submission)

        # 7 mock cases
        mock_visible_zaken_list = []
        for i in range(7):
            mock_zaak = MagicMock()
            mock_zaak.process_data.return_value = {
                "uuid": f"case-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "naam": f"Test zaak {i}",
                "api_group": api_group,
                "type_aanvraag": TypeAanvraag.ZAAK.value,
            }
            mock_visible_zaken_list.append(mock_zaak)

        mock_formulieren.return_value = mock_formulieren_list
        mock_visible_zaken.return_value = ZakenResult(
            zaken=mock_visible_zaken_list, skipped=[]
        )

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        # Test with num_zaken=5 (should get 3 formulieren + 2 zaken)
        response = self.client.get(url, {"num_zaken": "5"}, HTTP_HX_REQUEST="true")

        pyquery = PyQuery(response.content.decode("utf-8"))
        zaak_items = pyquery.find("oip-home-plugin-card")

        # Should return exactly 5 items
        self.assertEqual(len(zaak_items), 5)

        # Extract identifications (note: template uses 'identificatie' attribute)
        identifications = [pyquery(item).attr("identificatie") for item in zaak_items]

        # Verify formulieren come first
        self.assertIn("SUBMISSION-000", identifications)
        self.assertIn("SUBMISSION-001", identifications)
        self.assertIn("SUBMISSION-002", identifications)
        # Then zaken
        self.assertIn("ZAAK-000", identifications)
        self.assertIn("ZAAK-001", identifications)
        # But not the 3rd case
        self.assertNotIn("ZAAK-002", identifications)

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    def test_num_zaken_parameter_invalid_input(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        """Test that invalid values for num_zaken fall back to MAX_CASES_DEFAULT"""
        api_group = ZGWApiGroupConfigFactory()

        mock_visible_zaken_list = []
        for i in range(15):
            mock_zaak = MagicMock()
            mock_zaak.process_data.return_value = {
                "uuid": f"test-uuid-{i}",
                "identification": f"ZAAK-{i:03d}",
                "naam": f"Test zaak {i}",
                "api_group": api_group,
                "type_aanvraag": TypeAanvraag.ZAAK.value,
            }
            mock_visible_zaken_list.append(mock_zaak)

        mock_visible_zaken.return_value = ZakenResult(
            zaken=mock_visible_zaken_list, skipped=[]
        )

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)

        test_cases = ["invalid", "-5"]
        for invalid_num_zaken in test_cases:
            with self.subTest(invalid_num_zaken=invalid_num_zaken):
                response = self.client.get(
                    url, {"num_zaken": invalid_num_zaken}, HTTP_HX_REQUEST="true"
                )

                self.assertEqual(response.status_code, 200)

                pyquery = PyQuery(response.content.decode("utf-8"))
                zaak_items = pyquery.find("oip-home-plugin-card")
                # Should return MAX_CASES_DEFAULT
                self.assertEqual(len(zaak_items), MAX_CASES_DEFAULT)

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    def test_htmx_content_maps_naam_to_description(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_zaak = MagicMock()
        mock_zaak.process_data.return_value = {
            "uuid": "test-uuid-123",
            "identification": "ZAAK-001",
            "naam": "Dit is de naam van de zaak",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }
        mock_visible_zaken.return_value = ZakenResult(zaken=[mock_zaak], skipped=[])

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)

        pyquery = PyQuery(response.content.decode("utf-8"))
        zaak_item = pyquery.find("oip-home-plugin-card")

        # Verify naam is mapped to description attribute with Zaaknummer label
        self.assertIn("Zaaknummer", zaak_item.attr("description"))
        self.assertIn("ZAAK-001", zaak_item.attr("description"))

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    def test_htmx_content_handles_missing_optional_fields(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_zaak = MagicMock()
        # Return minimal data - identification is required for logging
        mock_zaak.process_data.return_value = {
            "uuid": "test-uuid-123",
            "identification": "",  # Required for logging
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }
        mock_visible_zaken.return_value = ZakenResult(zaken=[mock_zaak], skipped=[])

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)

        pyquery = PyQuery(response.content.decode("utf-8"))
        zaak_item = pyquery.find("oip-home-plugin-card")

        # Verify missing fields are provided as empty strings
        self.assertEqual(zaak_item.attr("identificatie"), "")
        self.assertEqual(zaak_item.attr("description"), "")

    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_formulieren")
    def test_htmx_content_handles_both_naam_and_description_fields(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        """
        Test that both 'naam' field (from formulieren) and 'description' field
        (from regular zaken) are correctly mapped to 'description' in the component output.
        Formulieren should have empty description, cases should show "Zaaknummer" label.
        """
        api_group = ZGWApiGroupConfigFactory()

        # Mock formulier with "naam" field
        mock_submission = MagicMock()
        mock_submission.process_data.return_value = {
            "uuid": "submission-uuid-1",
            "identification": "SUBMISSION-001",
            "naam": "Formulier met naam field",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.FORMULIER.value,
        }

        # Mock regular case with "description"
        mock_zaak = MagicMock()
        mock_zaak.process_data.return_value = {
            "uuid": "case-uuid-1",
            "identification": "ZAAK-001",
            "description": "Regular case met description field",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }

        mock_formulieren.return_value = [mock_submission]
        mock_visible_zaken.return_value = ZakenResult(zaken=[mock_zaak], skipped=[])

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})

        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)

        pyquery = PyQuery(response.content.decode("utf-8"))
        zaak_items = pyquery.find("oip-home-plugin-card")

        # Should have both items
        self.assertEqual(len(zaak_items), 2)

        # First item should be the formulier with empty description
        submission_item = zaak_items.eq(0)
        self.assertEqual(submission_item.attr("identificatie"), "SUBMISSION-001")
        self.assertEqual(submission_item.attr("description"), "")

        # Second item should be the case with "Zaaknummer" label
        case_item = zaak_items.eq(1)
        self.assertEqual(case_item.attr("identificatie"), "ZAAK-001")
        self.assertIn("Zaaknummer", case_item.attr("description"))
        self.assertIn("ZAAK-001", case_item.attr("description"))

    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken",
        return_value=ZakenResult(zaken=[], skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_formulieren")
    def test_formulier_uses_vervolg_link_as_url(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_submission = MagicMock()
        mock_submission.process_data.return_value = {
            "uuid": "submission-uuid-1",
            "identification": "SUBMISSION-001",
            "naam": "Test formulier",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.FORMULIER.value,
            "vervolg_link": "https://example.com/formulier/123",
        }
        mock_formulieren.return_value = [mock_submission]

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})
        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        pyquery = PyQuery(response.content.decode("utf-8"))
        item = pyquery.find("oip-home-plugin-card").eq(0)
        self.assertEqual(item.attr("detail-url"), "https://example.com/formulier/123")

    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken",
        return_value=ZakenResult(zaken=[], skipped=[]),
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_formulieren")
    def test_formulier_without_vervolg_link_has_empty_url(
        self, mock_formulieren, mock_fully_resolve, mock_visible_zaken
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_submission = MagicMock()
        mock_submission.process_data.return_value = {
            "uuid": "submission-uuid-1",
            "identification": "SUBMISSION-001",
            "naam": "Test formulier",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.FORMULIER.value,
            "vervolg_link": None,
        }
        mock_formulieren.return_value = [mock_submission]

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})
        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        pyquery = PyQuery(response.content.decode("utf-8"))
        item = pyquery.find("oip-home-plugin-card").eq(0)
        self.assertEqual(item.attr("detail-url"), "")

    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
        return_value=[],
    )
    @patch(
        "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
        side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
    )
    @patch("open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken")
    def test_zaak_uses_case_detail_url(
        self, mock_visible_zaken, mock_fully_resolve, mock_formulieren
    ):
        api_group = ZGWApiGroupConfigFactory()

        mock_zaak = MagicMock()
        mock_zaak.process_data.return_value = {
            "uuid": "zaak-uuid-1",
            "identification": "ZAAK-001",
            "naam": "Test zaak",
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }
        mock_visible_zaken.return_value = ZakenResult(zaken=[mock_zaak], skipped=[])

        plugin_model = cms_tools._init_plugin(CMSZakenPlugin, {"title": "Mijn Zaken"})
        url = reverse(
            "cms_plugins:zaken_content", kwargs={"plugin_id": plugin_model.pk}
        )

        self.client.force_login(self.user)
        response = self.client.get(url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        pyquery = PyQuery(response.content.decode("utf-8"))
        item = pyquery.find("oip-home-plugin-card").eq(0)
        detail_url = item.attr("detail-url")
        self.assertIn("/cases/", detail_url)
        self.assertIn("zaak-uuid-1", detail_url)
        self.assertIn("/status/", detail_url)
