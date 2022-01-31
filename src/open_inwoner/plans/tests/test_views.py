from django.urls import reverse

from django_webtest import WebTest
from webtest import Upload

from open_inwoner.accounts.tests.factories import ContactFactory, UserFactory

from .factories import PlanFactory


class PlanViewTests(WebTest):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.contact_user = UserFactory()
        self.contact = ContactFactory(contact_user=self.contact_user)
        self.plan = PlanFactory(title="plan_that_should_be_found", created_by=self.user)
        self.plan.contacts.add(self.contact)

        self.login_url = reverse("login")
        self.list_url = reverse("plans:plan_list")
        self.create_url = reverse("plans:plan_create")
        self.detail_url = reverse("plans:plan_detail", kwargs={"uuid": self.plan.uuid})
        self.goal_edit_url = reverse(
            "plans:plan_edit_goal", kwargs={"uuid": self.plan.uuid}
        )
        self.file_add_url = reverse(
            "plans:plan_add_file", kwargs={"uuid": self.plan.uuid}
        )
        self.action_add_url = reverse(
            "plans:plan_action_create", kwargs={"uuid": self.plan.uuid}
        )

    def test_plan_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_plan_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.title)

    def test_plan_contact_can_access(self):
        response = self.app.get(self.list_url, user=self.contact_user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.title)

    def test_plan_list_only_show_personal_actions(self):
        other_user = UserFactory()
        response = self.app.get(self.list_url, user=other_user)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.plan.title)

    def test_plan_goal_edit_login_required(self):
        response = self.app.get(self.goal_edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.goal_edit_url}")

    def test_plan_goal_edit(self):
        response = self.app.get(self.goal_edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.goal)
        form = response.forms["goal-edit"]
        form["goal"] = "editted goal"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.goal, "editted goal")

    def test_plan_goal_edit_contact_can_access(self):
        response = self.app.get(self.goal_edit_url, user=self.contact_user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.goal)
        form = response.forms["goal-edit"]
        form["goal"] = "editted goal"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.goal, "editted goal")

    def test_plan_goal_edit_not_your_action(self):
        other_user = UserFactory()
        response = self.app.get(self.goal_edit_url, user=other_user, status=404)

    def test_plan_file_add_login_required(self):
        response = self.app.get(self.file_add_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.file_add_url}")

    def test_plan_file_add(self):
        response = self.app.get(self.file_add_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["document-create"]
        form["file"] = Upload("filename.txt", b"contents")
        form["name"] = "file"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.plan.documents.count(), 1)

    def test_plan_file_add_contact_can_access(self):
        response = self.app.get(self.file_add_url, user=self.contact_user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["document-create"]
        form["file"] = Upload("filename.txt", b"contents")
        form["name"] = "file"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.plan.documents.count(), 1)

    def test_plan_file_add_not_your_action(self):
        other_user = UserFactory()
        response = self.app.get(self.file_add_url, user=other_user, status=404)

    def test_plan_action_create_login_required(self):
        response = self.app.get(self.action_add_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.action_add_url}")

    def test_plan_action_create(self):
        response = self.app.get(self.action_add_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]
        form["name"] = "action"
        form["description"] = "description"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.plan.actions.count(), 1)

    def test_plan_action_create_contact_can_access(self):
        response = self.app.get(self.action_add_url, user=self.contact_user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]
        form["name"] = "action"
        form["description"] = "description"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.plan.actions.count(), 1)

    def test_plan_action_create_not_your_action(self):
        other_user = UserFactory()
        response = self.app.get(self.action_add_url, user=other_user, status=404)

    def test_plan_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")
