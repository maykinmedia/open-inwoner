from django.test import TestCase, override_settings

import requests_mock

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.tests import cms_tools

from ..cms_plugins import TasksPlugin
from .mocks import TaakMockData


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TasksPluginTest(TestCase):
    def test_get_tasks_by_bsn(self, m):
        TaakMockData.setUpServices()
        mock_data = TaakMockData().install_mocks(m)

        user = DigidUserFactory(
            bsn=mock_data.mock_task_url_1["record"]["data"]["identificatie"]["value"]
        )
        # a taak for this user exists but should not be displayed
        DigidUserFactory(
            bsn=mock_data.mock_task_url_2["record"]["data"]["identificatie"]["value"]
        )

        html, context = cms_tools.render_plugin(TasksPlugin, plugin_data={}, user=user)

        tasks = context["tasks"]

        self.assertEqual(
            tasks,
            [
                {
                    "titel": "Test taak",
                    "status": "open",
                    "soort": "url",
                    "verloopdatum": "20 september 2025 18:25",
                    "identificatie": "123456789",
                    "koppeling": None,
                    "verwerker_taak_id": "18af0b6a-967b-4f81-bb8e-a44988e0c2f0",
                    "eigenaar": "OIP",
                    "task_url": "http://example.com/",
                }
            ],
        )
