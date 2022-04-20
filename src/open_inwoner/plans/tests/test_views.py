from unittest import expectedFailure

from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest
from webtest import Upload

from open_inwoner.accounts.tests.factories import (
    ActionFactory,
    ContactFactory,
    UserFactory,
)

from ..models import Plan
from .factories import ActionTemplateFactory, PlanFactory, PlanTemplateFactory


class PlanViewTests(WebTest):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.contact_user = UserFactory()
        self.contact = ContactFactory(
            contact_user=self.contact_user, created_by=self.user
        )
        self.plan = PlanFactory(title="plan_that_should_be_found", created_by=self.user)
        self.plan.contacts.add(self.contact)

        self.action = ActionFactory(plan=self.plan, created_by=self.user)

        self.login_url = reverse("login")
        self.list_url = reverse("plans:plan_list")
        self.create_url = reverse("plans:plan_create")
        self.detail_url = reverse("plans:plan_detail", kwargs={"uuid": self.plan.uuid})
        self.edit_url = reverse("plans:plan_edit", kwargs={"uuid": self.plan.uuid})
        self.goal_edit_url = reverse(
            "plans:plan_edit_goal", kwargs={"uuid": self.plan.uuid}
        )
        self.file_add_url = reverse(
            "plans:plan_add_file", kwargs={"uuid": self.plan.uuid}
        )
        self.action_add_url = reverse(
            "plans:plan_action_create", kwargs={"uuid": self.plan.uuid}
        )
        self.action_edit_url = reverse(
            "plans:plan_action_edit",
            kwargs={"plan_uuid": self.plan.uuid, "uuid": self.action.uuid},
        )
        self.export_url = reverse("plans:plan_export", kwargs={"uuid": self.plan.uuid})

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

        self.assertEqual(self.plan.actions.count(), 2)

    def test_plan_action_create_contact_can_access(self):
        response = self.app.get(self.action_add_url, user=self.contact_user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]
        form["name"] = "action"
        form["description"] = "description"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.plan.actions.count(), 2)

    def test_plan_action_create_not_your_action(self):
        other_user = UserFactory()
        response = self.app.get(self.action_add_url, user=other_user, status=404)

    def test_plan_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")

    def test_plan_create_fields_required(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors,
            {
                "title": [_("This field is required.")],
                "end_date": [_("This field is required.")],
            },
        )

    def test_plan_create_plan(self):
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["end_date"] = "2022-01-01"
        form["contacts"] = [self.contact.pk]
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, "")

    def test_plan_create_plan_with_template(self):
        plan_template = PlanTemplateFactory(file=None)
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["end_date"] = "2022-01-01"
        form["contacts"] = [self.contact.pk]
        form["template"] = plan_template.pk
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, plan_template.goal)
        self.assertEqual(plan.documents.count(), 0)
        self.assertEqual(plan.actions.count(), 0)

    def test_plan_create_plan_with_template_and_file(self):
        plan_template = PlanTemplateFactory()
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["end_date"] = "2022-01-01"
        form["contacts"] = [self.contact.pk]
        form["template"] = plan_template.pk
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, plan_template.goal)
        self.assertEqual(plan.documents.count(), 1)
        self.assertEqual(plan.actions.count(), 0)

    def test_plan_create_plan_with_template_and_actions(self):
        plan_template = PlanTemplateFactory(file=None)
        ActionTemplateFactory(plan_template=plan_template)
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["end_date"] = "2022-01-01"
        form["contacts"] = [self.contact.pk]
        form["template"] = plan_template.pk
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, plan_template.goal)
        self.assertEqual(plan.documents.count(), 0)
        self.assertEqual(plan.actions.count(), 1)

    def test_plan_edit_login_required(self):
        response = self.app.get(self.edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.edit_url}")

    def test_plan_edit_fields_required(self):
        response = self.app.get(self.edit_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = ""
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors,
            {
                "title": [_("This field is required.")],
            },
        )

    def test_plan_edit_plan(self):
        self.assertNotEqual(self.plan.title, "Plan title")
        response = self.app.get(self.edit_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan title"
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.title, "Plan title")

    def test_plan_action_edit_login_required(self):
        response = self.app.get(self.action_edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.action_edit_url}")

    def test_plan_action_edit(self):
        response = self.app.get(self.action_edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]
        form["name"] = "action name"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.action.refresh_from_db()
        self.assertEqual(self.action.name, "action name")

    def test_plan_export(self):
        response = self.app.get(self.export_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="plan_{self.plan.uuid}.pdf"',
        )

    def test_plan_export_login_required(self):
        response = self.app.get(self.export_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.export_url}")

    def test_plan_export_not_your_plan(self):
        other_user = UserFactory()
        response = self.app.get(self.export_url, user=other_user, status=404)
