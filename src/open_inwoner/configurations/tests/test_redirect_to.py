from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from ..models import SiteConfiguration


class TestRedirectTo(WebTest):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()

    def test_no_redirect(self):
        self.assertIsNone(self.config.redirect_to)
        self.app.get("/", status=200)

    def test_redirect_to_valid_path_succeeds_for_anonymous_user(self):
        self.config.redirect_to = "/accounts/login/"
        self.config.save()
        response = self.app.get("/")

        self.assertRedirects(response, reverse("login"))

    def test_redirect_to_valid_url_succeeds_for_anonymous_user(self):
        self.config.redirect_to = "https://www.example.com"
        self.config.save()
        response = self.app.get("/")

        self.assertEqual(response.location, self.config.redirect_to)

    def test_no_path_redirect_when_user_logged_in(self):
        user = UserFactory()
        self.config.redirect_to = "/accounts/login/"
        self.config.save()
        self.app.get("/", user=user, status=200)

    def test_no_url_redirect_when_user_logged_in(self):
        user = UserFactory()
        self.config.redirect_to = "https://www.example.com"
        self.config.save()
        self.app.get("/", user=user, status=200)
