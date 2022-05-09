from django.conf import settings
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory


class SessionBackendTest(WebTest):
    def setUp(self):
        self.url = reverse("sessions:restart-session")

    def test_default_session_length_when_not_logged_in(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.app.session._get_session().get("_session_expiry"), 900)

    def test_default_session_length_when_regular_user(self):
        user = UserFactory(is_staff=False)
        response = self.app.get(self.url, user=user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.app.session._get_session().get("_session_expiry"),
            settings.SESSION_COOKIE_AGE,
        )

    def test_extended_session_length_when_staff_user(self):
        user = UserFactory(is_staff=True)
        response = self.app.get(self.url, user=user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.app.session._get_session().get("_session_expiry"),
            settings.ADMIN_SESSION_COOKIE_AGE,
        )
