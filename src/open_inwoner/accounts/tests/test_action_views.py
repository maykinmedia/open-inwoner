from django.urls import reverse

from django_webtest import WebTest

from .factories import ActionFactory


class ActionViewTests(WebTest):
    def test_action_list_login_required(self):
        login_url = reverse("login")
        url = reverse("accounts:action_list")
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")

    def test_action_edit_login_required(self):
        action = ActionFactory()
        login_url = reverse("login")
        url = reverse("accounts:action_edit", kwargs={"uuid": action.uuid})
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")

    def test_action_create_login_required(self):
        login_url = reverse("login")
        url = reverse("accounts:action_create")
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")
