from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory


class ViewTest(WebTest):
    def setUp(self):
        self.url = reverse("sessions:restart-session")

    def test_when_not_logged_in(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_when_logged_in(self):
        user = UserFactory()
        response = self.app.get(self.url, user=user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"restarted")
