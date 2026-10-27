from django.test import TestCase, override_settings

import requests
import requests_mock
from freezegun import freeze_time

from open_inwoner.qmatic.services import get_appointments_for_user
from open_inwoner.qmatic.tests.data import QmaticMockData


@requests_mock.Mocker()
# QmaticMockData reverses 'profile:appointments', a CMS apphook URL
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class GetAppointmentsForUserTest(TestCase):
    def setUp(self):
        self.data = QmaticMockData()
        self.customers_url = (
            f"{self.data.api_root}appointment/customers/identify;{self.data.user.email}"
        )

    def test_returns_upcoming_appointments(self, m):
        self.data.setUpMocks(m)

        with freeze_time("2020-01-01 00:00"):
            appointments = get_appointments_for_user(self.data.user)

        self.assertEqual(
            [appointment.services[0].name for appointment in appointments],
            ["Paspoort", "ID kaart"],
        )

    def test_returns_nothing_without_verified_email(self, m):
        self.data.setUpMocks(m)
        self.data.user.verified_email = ""
        self.data.user.save()

        self.assertEqual(get_appointments_for_user(self.data.user), [])
        self.assertFalse(m.called)

    def test_returns_nothing_without_configured_service(self, m):
        self.data.config.service = None
        self.data.config.save()

        self.assertEqual(get_appointments_for_user(self.data.user), [])
        self.assertFalse(m.called)

    def test_returns_nothing_on_error_status(self, m):
        for status_code in (400, 401, 403, 500, 502, 503):
            with self.subTest(status_code=status_code):
                m.get(self.customers_url, status_code=status_code)

                self.assertEqual(get_appointments_for_user(self.data.user), [])

    def test_returns_nothing_on_request_exception(self, m):
        for exc in (requests.ConnectionError, requests.Timeout):
            with self.subTest(exc=exc.__name__):
                m.get(self.customers_url, exc=exc)

                self.assertEqual(get_appointments_for_user(self.data.user), [])
