from django.test import TestCase, override_settings

import requests_mock

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.plugins.cms_plugins import TasksPlugin
from open_inwoner.cms.tests import cms_tools

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
                    "soort": "externformulier",
                    "titel": "Externe Taak 1",
                    "status": "open",
                    "verloopdatum": "15 september 2025 23:59",
                    "koppeling": None,
                    "verwerker_taak_id": "0d59ada7-eacb-4129-8b7e-9907cd82c6d0",
                    "eigenaar": "OIP",
                    "task_url": "http://portaalformulier-url/formulier/startpagina?initial_data_reference=f58d9f41-78de-4d59-89ef-c439c5c24510",
                },
                {
                    "soort": "url",
                    "titel": "Url taak",
                    "status": "open",
                    "verloopdatum": "20 september 2025 18:25",
                    "koppeling": None,
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                    "eigenaar": "OIP",
                    "task_url": "http://www.url-task-example.nl/",
                },
            ],
        )

    def test_get_tasks_by_bsn_dimpact_only(self, m):
        TaakMockData.setUpServices()
        mock_data = TaakMockData().install_mocks(m)

        user = DigidUserFactory(
            bsn=mock_data.mock_task_data_url["identificatie"]["value"]
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
                    "soort": "url",
                    "titel": "Url taak",
                    "status": "open",
                    "verloopdatum": "20 september 2025 18:25",
                    "koppeling": None,
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                    "eigenaar": "OIP",
                    "task_url": "http://www.url-task-example.nl/",
                }
            ],
        )
