from django.urls import reverse

from django_webtest import WebTest

from .factories import ActionFactory, UserFactory


class ActionViewTests(WebTest):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.action = ActionFactory(
            name="action_that_should_be_found", created_by=self.user
        )

        self.login_url = reverse("login")
        self.list_url = reverse("accounts:action_list")
        self.edit_url = reverse(
            "accounts:action_edit", kwargs={"uuid": self.action.uuid}
        )
        self.create_url = reverse("accounts:action_create")

    def test_action_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_action_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.action.name)

    def test_action_list_only_show_personal_actions(self):
        other_user = UserFactory()
        response = self.app.get(self.list_url, user=other_user)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.action.name)

    def test_action_edit_login_required(self):
        response = self.app.get(self.edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.edit_url}")

    def test_action_edit(self):
        response = self.app.get(self.edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.action.name)

    def test_action_edit_not_your_action(self):
        other_user = UserFactory()
        response = self.app.get(self.edit_url, user=other_user, status=404)

    def test_action_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")
