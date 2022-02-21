from datetime import date

from django.urls import reverse

import freezegun
from django_webtest import WebTest

from ..choices import StatusChoices
from ..models import Action
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
        self.export_url = reverse(
            "accounts:action_export", kwargs={"uuid": self.action.uuid}
        )

    def test_action_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_action_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.action.name)

    def test_action_list_filter_created_by(self):
        action = ActionFactory(
            created_by=self.user, status=StatusChoices.closed, end_date=date.today()
        )
        action2 = ActionFactory(
            end_date="2021-04-02", status=StatusChoices.open, is_for=self.user
        )
        response = self.app.get(
            f"{self.list_url}?created_by={self.user.id}", user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["actions"]), [action, self.action])

    def test_action_list_filter_status(self):
        action = ActionFactory(
            created_by=self.user, status=StatusChoices.closed, end_date=date.today()
        )
        action2 = ActionFactory(
            end_date="2021-04-02", status=StatusChoices.open, is_for=self.user
        )
        self.assertEqual(Action.objects.count(), 3)
        response = self.app.get(
            f"{self.list_url}?status={StatusChoices.open}", user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["actions"]), [action2, self.action])

    def test_action_list_filter_end_date(self):
        action = ActionFactory(
            created_by=self.user, status=StatusChoices.closed, end_date=date.today()
        )
        action2 = ActionFactory(
            end_date="2021-04-02", status=StatusChoices.open, is_for=self.user
        )
        response = self.app.get(f"{self.list_url}?end_date=02-04-2021", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["actions"]), [action2])

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

    def test_action_export(self):
        response = self.app.get(self.export_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="action_{self.action.uuid}.pdf"',
        )

    def test_action_export_login_required(self):
        response = self.app.get(self.export_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")

    def test_action_export_not_your_action(self):
        other_user = UserFactory()
        response = self.app.get(self.export_url, user=other_user, status=404)
