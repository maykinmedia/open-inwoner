from django.contrib.messages import get_messages
from django.core import mail
from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest
from webtest import Upload

from open_inwoner.accounts.models import Action
from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory

from ..models import Plan
from .factories import ActionTemplateFactory, PlanFactory, PlanTemplateFactory


class PlanViewTests(WebTest):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.contact = UserFactory()
        self.user.user_contacts.add(self.contact)
        self.plan = PlanFactory(title="plan_that_should_be_found", created_by=self.user)
        self.plan.plan_contacts.add(self.user)
        self.plan.plan_contacts.add(self.contact)

        self.action = ActionFactory(plan=self.plan, created_by=self.user)
        self.action_deleted = ActionFactory(
            plan=self.plan, created_by=self.user, is_deleted=True
        )

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
        self.action_delete_url = reverse(
            "plans:plan_action_delete",
            kwargs={"plan_uuid": self.plan.uuid, "uuid": self.action.uuid},
        )
        self.export_url = reverse("plans:plan_export", kwargs={"uuid": self.plan.uuid})

    def test_plan_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_creator_is_added_when_create_plan(self):
        plan = PlanFactory.build()
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = plan.title
        form["end_date"] = plan.end_date
        response = form.submit()
        created_plan = Plan.objects.get(title=plan.title)
        self.assertEqual(created_plan.plan_contacts.get(), self.user)
        self.assertEqual(created_plan.created_by, self.user)

    def test_plan_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.title)

    def test_plan_detail_contacts(self):
        response = self.app.get(self.detail_url, user=self.user)
        self.assertContains(response, self.contact.get_full_name())
        self.assertContains(response, self.user.get_full_name())

        response = self.app.get(self.detail_url, user=self.contact)
        self.assertContains(response, self.user.get_full_name())
        self.assertContains(response, self.contact.get_full_name())

        # Contact for one user, but not the other
        # Check if all users can see eachother in the plan
        new_contact = UserFactory()
        self.user.user_contacts.add(new_contact)
        self.plan.plan_contacts.add(new_contact)

        response = self.app.get(self.detail_url, user=self.user)
        self.assertContains(response, self.contact.get_full_name())
        self.assertContains(response, new_contact.get_full_name())
        self.assertContains(response, self.user.get_full_name())

        response = self.app.get(self.detail_url, user=self.contact)
        self.assertContains(response, self.user.get_full_name())
        self.assertContains(response, self.contact.get_full_name())
        self.assertContains(response, new_contact.get_full_name())

        response = self.app.get(self.detail_url, user=new_contact)
        self.assertContains(response, self.user.get_full_name())
        self.assertContains(response, new_contact.get_full_name())
        self.assertContains(response, self.contact.get_full_name())

        new_contact.delete()

        # Verify that without being added to the plan the contact isn't visible
        new_contact = UserFactory()
        self.user.user_contacts.add(new_contact)

        response = self.app.get(self.detail_url, user=self.user)
        self.assertContains(response, self.contact.get_full_name())
        self.assertNotContains(response, new_contact.get_full_name())

    def test_plan_contact_can_access(self):
        response = self.app.get(self.list_url, user=self.contact)
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
        response = self.app.get(self.goal_edit_url, user=self.contact)
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
        self.app.get(self.goal_edit_url, user=other_user, status=404)

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
        response = self.app.get(self.file_add_url, user=self.contact)
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

        self.assertEqual(self.plan.actions.visible().count(), 2)

    def test_plan_action_create_contact_can_access(self):
        response = self.app.get(self.action_add_url, user=self.contact)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]
        form["name"] = "action"
        form["description"] = "description"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.plan.actions.visible().count(), 2)

    def test_plan_action_create_not_your_action(self):
        other_user = UserFactory()
        self.app.get(self.action_add_url, user=other_user, status=404)

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
        form["plan_contacts"] = [self.contact.pk]
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
        form["plan_contacts"] = [self.contact.pk]
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
        form["plan_contacts"] = [self.contact.pk]
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
        form["plan_contacts"] = [self.contact.pk]
        form["template"] = plan_template.pk
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, plan_template.goal)
        self.assertEqual(plan.documents.count(), 0)
        self.assertEqual(plan.actions.count(), 1)

    def test_plan_create_plan_validation_error_reselects_template_and_contact(self):
        plan_template = PlanTemplateFactory(file=None)
        ActionTemplateFactory(plan_template=plan_template)
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["end_date"] = ""  # empty end_date so validation fails
        form["contacts"] = [self.contact.pk]
        form["template"] = plan_template.pk
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        # nothing was created
        self.assertEqual(Plan.objects.count(), 1)

        # check if we reselected the template and contact
        elem = response.pyquery(f"#id_template_{plan_template.id}")[0]
        self.assertEqual(elem.attrib.get("checked"), "checked")

        # NOTE: custom widget ID hardcoded on index of choice
        elem = response.pyquery(f"#id_contacts_1")[0]
        self.assertEqual(elem.attrib.get("checked"), "checked")

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
        # breakpoint()
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.title, "Plan title")

    def test_plan_action_edit_login_required(self):
        response = self.app.get(self.action_edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.action_edit_url}")

    def test_plan_action_edit_deleted_action(self):
        url = reverse(
            "plans:plan_action_edit",
            kwargs={"plan_uuid": self.plan.uuid, "uuid": self.action_deleted.uuid},
        )
        self.app.get(url, user=self.user, status=404)

    def test_plan_action_edit(self):
        response = self.app.get(self.action_edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]
        form["name"] = "action name"

        response = form.submit(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.action.refresh_from_db()
        self.assertEqual(self.action.name, "action name")

        # send notification to the contact
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "Plan action has been updated at Open Inwoner Platform"
        )
        self.assertEqual(email.to, [self.contact.email])
        plan_url = f"http://testserver{self.detail_url}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(plan_url, body)
        self.assertIn("Changed: Naam.", body)

    def test_plan_action_edit_not_changed(self):
        response = self.app.get(self.action_edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]

        response = form.submit(user=self.user)

        self.assertEqual(response.status_code, 302)

        # no notification is sent
        self.assertEqual(len(mail.outbox), 0)

    def test_plan_action_delete_login_required_http_403(self):
        response = self.client.post(self.action_delete_url)
        self.assertEquals(response.status_code, 403)

    def test_plan_action_delete_http_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.action_delete_url)
        self.assertEqual(response.status_code, 405)

    def test_plan_action_delete(self):
        self.client.force_login(self.user)
        response = self.client.post(self.action_delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.detail_url)

        # Action is now marked as .is_deleted (and not actually deleted)
        action = Action.objects.get(id=self.action.id)
        self.assertTrue(action.is_deleted)

        # django message to user
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        expected = _("Actie '{action}' is verwijdered.").format(action=self.action)
        self.assertEqual(str(messages[0]), expected)

        # email is sent to out contact
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject, "Plan action has been updated at Open Inwoner Platform"
        )
        self.assertEqual(email.to, [self.contact.email])
        plan_url = f"http://testserver{self.detail_url}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(plan_url, body)

    def test_plan_action_delete_not_your_action(self):
        other_user = UserFactory()
        self.client.force_login(other_user)
        response = self.client.post(self.action_delete_url)
        self.assertEqual(response.status_code, 404)

    def test_plan_export(self):
        response = self.app.get(self.export_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="plan_{self.plan.uuid}.pdf"',
        )
        self.assertEqual(list(response.context["actions"]), [self.action])

    def test_plan_export_login_required(self):
        response = self.app.get(self.export_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.export_url}")

    def test_plan_export_not_your_plan(self):
        other_user = UserFactory()
        self.app.get(self.export_url, user=other_user, status=404)
