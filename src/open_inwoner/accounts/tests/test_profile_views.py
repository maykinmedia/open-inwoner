from django.urls import reverse

from django_webtest import WebTest


class ProfileViewTests(WebTest):
    def test_login_required(self):
        login_url = reverse("login")
        url = reverse("accounts:my_profile")
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")
