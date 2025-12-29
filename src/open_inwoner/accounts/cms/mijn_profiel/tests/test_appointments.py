from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from freezegun import freeze_time
from pyquery import PyQuery

from open_inwoner.accounts.cms.mijn_profiel.cms_plugins import UserAppointmentsPlugin
from open_inwoner.core.cms.utils import cms_test_utils as cms_tools
from open_inwoner.qmatic.tests.data import QmaticMockData


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.core.cms.tests.urls")
class TestUserAppointmentsPlugin(TestCase):
    def test_plugin(self, m):
        data = QmaticMockData()
        data.setUpMocks(m)

        self.assertTrue(data.user.has_verified_email())

        with freeze_time("2020-01-01 00:00"):
            html, context = cms_tools.render_plugin(
                UserAppointmentsPlugin, plugin_data={}, user=data.user
            )

        appointments = context["appointments"]

        self.assertEqual(len(appointments), 2)

        self.assertIn("Paspoort", html)
        self.assertIn("ID kaart", html)
        self.assertNotIn("Old appointment", html)

        pyquery = PyQuery(html)

        # test item
        items = pyquery.find("oip-home-plugin-card")
        self.assertEqual(len(items), 2)

        aanvraag_paspoort_date = items[0].attrib["date"]
        aanvraag_paspoort_title = items[0].attrib["status"]
        aanvraag_id_kaart_date = items[1].attrib["date"]
        aanvraag_id_kaart_title = items[1].attrib["status"]

        self.assertEqual(aanvraag_paspoort_date, "1 januari 2020 om 13:00")
        self.assertEqual(aanvraag_paspoort_title, "Paspoort")
        self.assertEqual(aanvraag_id_kaart_date, "6 maart 2020 om 11:30")
        self.assertEqual(aanvraag_id_kaart_title, "ID kaart")

        action_url = items[0].attrib["detail-url"]
        self.assertEqual(action_url, reverse("profile:appointments"))

    def test_plugin__email_not_verified(self, m):
        data = QmaticMockData()
        data.setUpMocks(m)
        data.user.verified_email = ""
        data.user.save()
        self.assertFalse(data.user.has_verified_email())

        html, context = cms_tools.render_plugin(
            UserAppointmentsPlugin, plugin_data={}, user=data.user
        )

        appointments = context["appointments"]

        # zero results
        self.assertEqual(len(appointments), 0)
