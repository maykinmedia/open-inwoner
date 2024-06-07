from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from pyquery import PyQuery as PQ

from open_inwoner.cms.tests import cms_tools
from open_inwoner.qmatic.tests.data import QmaticMockData

from ..cms_plugins import UserAppointmentsPlugin


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestUserAppointmentsPlugin(TestCase):
    def test_plugin(self, m):
        data = QmaticMockData()
        data.setUpMocks(m)

        self.assertTrue(data.user.has_verified_email())

        html, context = cms_tools.render_plugin(
            UserAppointmentsPlugin, plugin_data={}, user=data.user
        )

        appointments = context["appointments"]

        self.assertEqual(len(appointments), 2)

        self.assertIn("Paspoort", html)
        self.assertIn("ID kaart", html)

        pyquery = PQ(html)

        # test item
        items = pyquery.find(".card-container .card")
        self.assertEqual(len(items), 2)

        aanvraag_paspoort_date = PQ(items.find("p.tabled__value")[0]).text()
        aanvraag_paspoort_title = PQ(items.find(".plugin-card__heading")[0]).text()
        aanvraag_id_kaart_date = PQ(items.find("p.tabled__value")[1]).text()
        aanvraag_id_kaart_title = PQ(items.find(".plugin-card__heading")[1]).text()

        self.assertEqual(aanvraag_paspoort_date, "1 januari 2020 om 13:00 uur")
        self.assertEqual(aanvraag_paspoort_title, "Paspoort")
        self.assertEqual(aanvraag_id_kaart_date, "6 maart 2020 om 11:30 uur")
        self.assertEqual(aanvraag_id_kaart_title, "ID kaart")

        action_url = items[0].attrib["href"]
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
