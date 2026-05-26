from django.test import TestCase, override_settings

import requests_mock
from requests.exceptions import ConnectionError as RequestsConnectionError

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.cms.plugins.cms_plugins import TasksPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.openzaak.tests.mocks import ESuiteTaskData
from open_inwoner.openzaak.tests.shared import FORMS_ROOT

from .mocks import (
    UUID_OBJECT_TYPE_DIENSVERLENING_1,
    UUID_OBJECT_TYPE_DIMPACT,
    TaakMockData,
)


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TasksPluginTest(TestCase):
    def test_get_tasks_by_bsn_all_types(self, m):
        TaakMockData.setUpServices()
        mock_data = TaakMockData().install_mocks(m)

        user = DigidUserFactory(
            bsn=mock_data.mock_task_data_externformulier_1["betrokkene"]["authorizee"][
                "legalSubject"
            ]["identifier"]
        )
        # should be filtered out (BSN)
        DigidUserFactory(
            bsn=mock_data.mock_task_data_externformulier_2["betrokkene"]["authorizee"][
                "legalSubject"
            ]["identifier"]
        )

        html, context = cms_tools.render_plugin(
            TasksPlugin,
            plugin_data={
                "object_type_dimpact": UUID_OBJECT_TYPE_DIMPACT,
                "object_type_generieke_dienstverlening": UUID_OBJECT_TYPE_DIENSVERLENING_1,
            },
            user=user,
        )

        tasks = context["tasks"]

        self.assertEqual(
            tasks,
            [
                {
                    "api_source": "Objects API",
                    "soort": "url",
                    "titel": "Url taak",
                    "status": "open",
                    "verloopdatum": "20 september 2025 18:25",
                    "koppeling": None,
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                    "eigenaar": "OIP",
                    "task_url": "http://www.url-task-example.nl/",
                },
                {
                    "api_source": "Objects API",
                    "soort": "externformulier",
                    "titel": "Externe Taak 1",
                    "status": "open",
                    "verloopdatum": "15 september 2025 23:59",
                    "koppeling": None,
                    "verwerker_taak_id": "0d59ada7-eacb-4129-8b7e-9907cd82c6d0",
                    "eigenaar": "OIP",
                    "task_url": "http://portaalformulier-url/formulier/startpagina?initial_data_reference=f58d9f41-78de-4d59-89ef-c439c5c24510",
                },
            ],
        )

    def test_get_tasks_by_bsn_dimpact_only(self, m):
        TaakMockData.setUpServices()
        mock_data = TaakMockData().install_mocks(m)

        user = DigidUserFactory(
            bsn=mock_data.mock_task_data_externformulier_1["betrokkene"]["authorizee"][
                "legalSubject"
            ]["identifier"]
        )
        # should be filtered out (BSN) - using a different BSN
        DigidUserFactory(
            bsn=mock_data.mock_task_data_externformulier_2["betrokkene"]["authorizee"][
                "legalSubject"
            ]["identifier"]
        )

        html, context = cms_tools.render_plugin(
            TasksPlugin,
            plugin_data={"object_type_dimpact": UUID_OBJECT_TYPE_DIMPACT},
            user=user,
        )

        tasks = context["tasks"]

        self.assertEqual(
            tasks,
            [
                {
                    "api_source": "Objects API",
                    "soort": "externformulier",
                    "titel": "Externe Taak 1",
                    "status": "open",
                    "verloopdatum": "15 september 2025 23:59",
                    "koppeling": None,
                    "verwerker_taak_id": "0d59ada7-eacb-4129-8b7e-9907cd82c6d0",
                    "eigenaar": "OIP",
                    "task_url": "http://portaalformulier-url/formulier/startpagina?initial_data_reference=f58d9f41-78de-4d59-89ef-c439c5c24510",
                }
            ],
        )

    def test_tasks_plugin_renders_zgw_taken(self, m):
        """
        Test that TasksPlugin correctly fetches and displays ZGW tasks
        """
        ZGWApiGroupConfigFactory(form_service__api_root=FORMS_ROOT)

        ESuiteTaskData().install_mocks(m)

        user = DigidUserFactory(bsn="111222333")

        html, context = cms_tools.render_plugin(
            TasksPlugin,
            plugin_data={},
            user=user,
        )

        tasks = context["tasks"]

        self.assertEqual(len(tasks), 2)

        self.assertEqual(tasks[0]["api_source"], "ZGW API")
        self.assertEqual(tasks[0]["task_url"], "https://maykinmedia.nl")
        self.assertEqual(tasks[0]["status"], "open")
        self.assertEqual(tasks[0]["titel"], "Aanvullende informatie gewenst")

        self.assertEqual(tasks[1]["task_url"], "https://maykinmedia.nl")
        self.assertEqual(tasks[1]["status"], "open")
        self.assertEqual(tasks[1]["titel"], "Aanvullende informatie gewenst")

        self.assertIn("Aanvullende informatie gewenst", html)
        self.assertIn("Status: open", html)

    def test_tasks_plugin_handles_zgw_api_errors(self, m):
        """
        Test that ZGW API errors don't break the plugin
        """
        ZGWApiGroupConfigFactory(form_service__api_root=FORMS_ROOT)

        m.get(f"{FORMS_ROOT}openstaande-taken", exc=RequestsConnectionError)

        user = DigidUserFactory(bsn="111222333")

        html, context = cms_tools.render_plugin(
            TasksPlugin,
            plugin_data={},
            user=user,
        )

        tasks = context["tasks"]

        self.assertEqual(len(tasks), 0)

    def test_tasks_plugin_combines_objects_and_zgw_tasks(self, m):
        """
        Test that both task sources are merged correctly
        """
        TaakMockData.setUpServices()
        mock_data = TaakMockData().install_mocks(m)

        ZGWApiGroupConfigFactory(form_service__api_root=FORMS_ROOT)
        ESuiteTaskData().install_mocks(m)

        user = DigidUserFactory(
            bsn=mock_data.mock_task_data_externformulier_1["betrokkene"]["authorizee"][
                "legalSubject"
            ]["identifier"]
        )

        html, context = cms_tools.render_plugin(
            TasksPlugin,
            plugin_data={
                "object_type_dimpact": UUID_OBJECT_TYPE_DIMPACT,
                "object_type_generieke_dienstverlening": UUID_OBJECT_TYPE_DIENSVERLENING_1,
            },
            user=user,
        )

        tasks = context["tasks"]

        self.assertEqual(len(tasks), 4)

        # Separate tasks by type: ZGW tasks have empty soort, Objects API tasks have values
        zgw_tasks = [t for t in tasks if t.get("soort") == ""]
        objects_api_tasks = [t for t in tasks if t.get("soort") != ""]

        # Verify we have 2 Objects API tasks
        self.assertEqual(len(objects_api_tasks), 2)
        self.assertEqual(objects_api_tasks[0]["titel"], "Url taak")
        self.assertEqual(objects_api_tasks[0]["soort"], "url")
        self.assertEqual(objects_api_tasks[1]["titel"], "Externe Taak 1")
        self.assertEqual(objects_api_tasks[1]["soort"], "externformulier")

        # Verify we have 2 ZGW tasks
        self.assertEqual(len(zgw_tasks), 2)
        self.assertEqual(zgw_tasks[0]["titel"], "Aanvullende informatie gewenst")
        self.assertEqual(zgw_tasks[0]["status"], "open")
        self.assertEqual(zgw_tasks[0]["soort"], "")
        self.assertEqual(zgw_tasks[1]["titel"], "Aanvullende informatie gewenst")
        self.assertEqual(zgw_tasks[1]["status"], "open")
        self.assertEqual(zgw_tasks[1]["soort"], "")

    def test_tasks_plugin_only_for_bsn_users(self, m):
        """
        Test that ZGW tasks are only fetched for users with BSN
        """
        ZGWApiGroupConfigFactory(form_service__api_root=FORMS_ROOT)
        ESuiteTaskData().install_mocks(m)

        # Create eHerkenning user
        user = eHerkenningUserFactory(kvk="12345678")

        html, context = cms_tools.render_plugin(
            TasksPlugin,
            plugin_data={},
            user=user,
        )

        tasks = context["tasks"]

        # Should have no tasks because eHerkenning users don't get ZGW tasks
        self.assertEqual(len(tasks), 0)
