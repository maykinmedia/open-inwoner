from datetime import date

from django.contrib.messages import get_messages
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest
from freezegun import freeze_time
from webtest import Upload

from open_inwoner.accounts.choices import ContactTypeChoices, StatusChoices
from open_inwoner.accounts.models import Action
from open_inwoner.accounts.tests.factories import (
    ActionFactory,
    DocumentFactory,
    UserFactory,
)
from open_inwoner.accounts.tests.test_action_views import ActionsPlaywrightTests
from open_inwoner.utils.tests.playwright import multi_browser

from ..models import Plan, PlanContact
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
        self.action_history_url = reverse(
            "plans:plan_action_history",
            kwargs={"plan_uuid": self.plan.uuid, "uuid": self.action.uuid},
        )
        self.action_edit_status_url = reverse(
            "plans:plan_action_edit_status",
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
        form["goal"] = plan.goal
        form["end_date"] = plan.end_date
        form["plan_contacts"] = [self.contact.pk]
        response = form.submit()

        created_plan = Plan.objects.get(title=plan.title)

        self.assertIn(self.user, created_plan.plan_contacts.all())
        self.assertEqual(created_plan.created_by, self.user)

        contact = PlanContact.objects.last()
        self.assertEqual(contact.user, self.user)
        self.assertEqual(contact.notify_new, True)

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

    def test_plan_doesnt_show_action_status_button_for_actions_not_connected_to_plan_contacts(
        self,
    ):
        self.action.is_for = self.user
        self.action.save()

        # note self.user is connected to the action
        self.assertTrue(self.action.is_connected(self.user))

        # but contact user is only connected to the plan (and not the action)
        self.assertFalse(self.action.is_connected(self.contact))

        button_selector = f"#actions_{self.action.id}__status .actions__status-button"

        # list our connected action
        response = self.app.get(self.detail_url, user=self.user)
        self.assertEqual(list(response.context["actions"]), [self.action])

        # we have the button
        self.assertNotEqual(list(response.pyquery(button_selector)), [])

        # list actions part of the contact user's connection to the plan
        response = self.app.get(self.detail_url, user=self.contact)
        self.assertEqual(list(response.context["actions"]), [self.action])

        # action is there but there is no button for the contact
        self.assertEqual(list(response.pyquery(button_selector)), [])

    def test_plan_goal_edit_login_required(self):
        response = self.app.get(self.goal_edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.goal_edit_url}")

    def test_plan_goal_edit(self):
        response = self.app.get(self.goal_edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.goal)
        self.assertContains(response, self.plan.description)
        form = response.forms["goal-edit"]
        form["goal"] = "editted goal"
        form["description"] = "editted description"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.goal, "editted goal")
        self.assertEqual(self.plan.description, "editted description")

    def test_plan_goal_edit_contact_can_access(self):
        response = self.app.get(self.goal_edit_url, user=self.contact)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.goal)
        form = response.forms["goal-edit"]
        form["goal"] = "editted goal"
        form["description"] = "editted description"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.goal, "editted goal")
        self.assertEqual(self.plan.description, "editted description")

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

    def test_plan_file_can_be_downloaded_by_contact(self):
        doc = DocumentFactory(owner=self.user, plan=self.plan)
        response = self.app.get(
            reverse("accounts:documents_download", kwargs={"uuid": doc.uuid}),
            user=self.contact,
        )
        self.assertEqual(response.status_code, 200)

    def test_plan_file_cannot_be_downloaded_by_non_contact(self):
        doc = DocumentFactory(owner=self.user, plan=self.plan)
        new_user = UserFactory()
        self.app.get(
            reverse("accounts:documents_download", kwargs={"uuid": doc.uuid}),
            user=new_user,
            status=403,
        )

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
                "__all__": [_("At least one collaborator is required for a plan.")],
            },
        )

    def test_plan_create_fails_with_no_collaborators(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["goal"] = "Goal"
        form["description"] = "Description"
        form["end_date"] = "2022-01-01"
        response = form.submit()

        self.assertEqual(Plan.objects.count(), 1)
        self.assertEqual(
            response.context["form"].errors,
            {"__all__": [_("At least one collaborator is required for a plan.")]},
        )

    def test_plan_create_contains_expected_contacts(self):
        another_contact = UserFactory()
        self.user.user_contacts.add(another_contact)
        response = self.app.get(self.create_url, user=self.user)

        rendered_contacts = response.pyquery("#plan-form .grid .form__grid-box")[
            0
        ].text_content()

        self.assertNotIn(self.user.get_full_name(), rendered_contacts)
        self.assertIn(self.contact.get_full_name(), rendered_contacts)
        self.assertIn(another_contact.get_full_name(), rendered_contacts)

    def test_plan_create_plan(self):
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["goal"] = "Goal"
        form["description"] = "Description"
        form["end_date"] = "2022-01-01"
        form["plan_contacts"] = [self.contact.pk]
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, "Goal")
        self.assertEqual(plan.description, "Description")

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
        self.assertEqual(plan.description, plan_template.description)
        self.assertEqual(plan.documents.count(), 0)
        self.assertEqual(plan.actions.count(), 0)

    def test_plan_create_plan_with_template_and_field_overrides(self):
        plan_template = PlanTemplateFactory(file=None)
        self.assertEqual(Plan.objects.count(), 1)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["goal"] = "Goal"
        form["description"] = "Description"
        form["end_date"] = "2022-01-01"
        form["plan_contacts"] = [self.contact.pk]
        form["template"] = plan_template.pk
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Plan.objects.count(), 2)
        plan = Plan.objects.exclude(pk=self.plan.id).first()
        self.assertEqual(plan.title, "Plan")
        self.assertEqual(plan.goal, "Goal")
        self.assertEqual(plan.description, "Description")
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
        self.assertEqual(plan.description, plan_template.description)
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
        self.assertEqual(plan.description, plan_template.description)
        self.assertEqual(plan.documents.count(), 0)
        self.assertEqual(plan.actions.count(), 1)

    def test_plan_create_plan_validation_error_reselects_template_and_contact(self):
        plan_template = PlanTemplateFactory(file=None)
        ActionTemplateFactory(plan_template=plan_template)
        # make sure we have only one plan
        self.assertEqual(Plan.objects.count(), 1)

        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["plan-form"]
        form["title"] = "Plan"
        form["end_date"] = ""  # empty end_date so validation fails
        form["plan_contacts"] = [str(self.contact.pk)]
        form["template"] = str(plan_template.pk)
        response = form.submit()
        self.assertEqual(response.status_code, 200)

        # nothing was created
        self.assertEqual(Plan.objects.count(), 1)

        # check if we reselected the template and contact
        elem = response.pyquery(f"#id_template_{plan_template.id}")[0]
        self.assertEqual(elem.attrib.get("checked"), "checked")

        # NOTE: custom widget ID hardcoded on index of choice
        elem = response.pyquery(f"#id_plan_contacts_1")[0]
        self.assertEqual(elem.attrib.get("checked"), "checked")

    @override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
    def test_plan_create_contains_contact_create_link_when_no_contacts_exist(self):
        self.user.user_contacts.remove(self.contact)
        response = self.app.get(self.create_url, user=self.user)
        self.assertContains(response, reverse("profile:contact_create"))

    @override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
    def test_plan_create_does_not_contain_contact_create_link_when_contacts_exist(
        self,
    ):
        response = self.app.get(self.create_url, user=self.user)
        self.assertNotContains(response, reverse("profile:contact_create"))

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
        self.assertIn("Gewijzigd: Naam.", body)

    def test_plan_action_edit_not_changed(self):
        response = self.app.get(self.action_edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["action-create"]

        response = form.submit(user=self.user)

        self.assertEqual(response.status_code, 302)

        # no notification is sent
        self.assertEqual(len(mail.outbox), 0)

    def test_plan_actions_history_breadcrumbs(self):
        response = self.app.get(self.action_history_url, user=self.user)
        crumbs = response.pyquery(".breadcrumbs__list-item")
        self.assertIn(_("Samenwerking"), crumbs[1].text_content())
        self.assertIn(self.plan.title, crumbs[2].text_content())
        self.assertIn(self.action.name, crumbs[3].text_content())

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

    def test_plan_action_status(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.action_edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, StatusChoices.closed)

    def test_plan_action_status_requires_htmx_header(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.action_edit_status_url,
            {"status": StatusChoices.closed},
        )
        self.assertEqual(response.status_code, 400)

    def test_plan_action_status_invalid_post_data(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.action_edit_status_url,
            {"not_the_parameter": 123},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 400)

    def test_plan_action_status_http_get_disallowed(self):
        self.client.force_login(self.user)
        response = self.client.get(
            self.action_edit_status_url,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 405)

    def test_plan_action_status_login_required(self):
        response = self.client.post(
            self.action_edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 403)

    def test_plan_action_status_not_your_action(self):
        other_user = UserFactory()
        self.client.force_login(other_user)
        response = self.client.post(
            self.action_edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 404)


class PlanBegeleiderListViewTests(WebTest):
    def setUp(self):
        self.contact = UserFactory()
        self.begeleider = UserFactory(contact_type=ContactTypeChoices.begeleider)
        self.begeleider.user_contacts.add(self.contact)
        self.begeleider_plan = PlanFactory(
            title="begeleider plan_that_should_be_found", created_by=self.begeleider
        )
        self.begeleider_plan.plan_contacts.add(self.begeleider)
        self.begeleider_plan.plan_contacts.add(self.contact)
        self.begeleider_action = ActionFactory(
            plan=self.begeleider_plan, created_by=self.begeleider
        )
        self.login_url = reverse("login")
        self.list_url = reverse("plans:plan_list")

    @freeze_time("2022-01-01")
    def test_plan_list_renders_template_for_begeleider(self):
        self.begeleider_plan.end_date = date(2022, 1, 20)
        self.begeleider_plan.save()

        response = self.app.get(self.list_url, user=self.begeleider)
        extended = response.pyquery(".plans-extended")

        self.assertEqual(len(extended), 1)

    @freeze_time("2022-01-01")
    def test_plan_list_renders_expected_data(self):
        self.begeleider_plan.end_date = date(2022, 1, 20)
        self.begeleider_plan.save()

        response = self.app.get(self.list_url, user=self.begeleider)
        rendered_plan_title = response.pyquery("tbody .table__header")[0].text_content()
        items = response.pyquery("tbody .table__item")
        rendered_contact = items[0].text
        rendered_end_date = items[1].text
        rendered_plan_status = items[2].text
        rendered_actions_num = items[3].text
        rendered_action_required = response.pyquery(
            "tbody .table__item--notification-danger"
        )[0].text

        self.assertIn(self.begeleider_plan.title, rendered_plan_title)
        self.assertEqual(rendered_contact, self.contact.get_full_name())
        self.assertEqual(rendered_end_date, "20-01-2022")
        self.assertEqual(rendered_plan_status, _("Open"))
        self.assertEqual(rendered_actions_num, "1")
        self.assertEqual(rendered_action_required, _("Actie vereist"))

    @freeze_time("2022-01-01")
    def test_plan_list_renders_expected_data_for_expired_plan(self):
        self.begeleider_plan.end_date = date(2022, 1, 1)
        self.begeleider_plan.save()

        response = self.app.get(self.list_url, user=self.begeleider)
        items = response.pyquery("tbody .table__item")
        rendered_end_date = items[1].text
        rendered_plan_status = items[2].text

        self.assertEqual(rendered_end_date, "01-01-2022")
        self.assertEqual(rendered_plan_status, _("Afgerond"))

    @freeze_time("2022-01-01")
    def test_plan_list_renders_expected_data_for_approval_actions(self):
        self.begeleider_action.status = StatusChoices.approval
        self.begeleider_action.save()

        response = self.app.get(self.list_url, user=self.begeleider)
        rendered_actions_num = response.pyquery("tbody .table__item")[3].text
        rendered_action_required = response.pyquery(
            "tbody .table__item--notification-danger"
        )[0].text

        self.assertEqual(rendered_actions_num, "1")
        self.assertEqual(rendered_action_required, _("Actie vereist"))

    @freeze_time("2022-01-01")
    def test_plan_list_renders_expected_data_for_closed_actions(self):
        self.begeleider_action.status = StatusChoices.closed
        self.begeleider_action.save()

        response = self.app.get(self.list_url, user=self.begeleider)
        rendered_actions_num = response.pyquery("tbody .table__item")[3].text
        rendered_action_required = response.pyquery(
            "tbody .table__item--notification-danger"
        )

        self.assertEqual(rendered_actions_num, "0")
        self.assertEqual(rendered_action_required, [])

    def test_plan_list_doesnt_add_deleted_action_to_total(self):
        self.begeleider_action.is_deleted = True
        self.begeleider_action.save()

        response = self.app.get(self.list_url, user=self.begeleider)
        rendered_actions_num = response.pyquery("tbody .table__item")[3].text
        rendered_action_required = response.pyquery(
            "tbody .table__item--notification-danger"
        )

        self.assertEqual(rendered_actions_num, "0")
        self.assertEqual(rendered_action_required, [])

    def test_plan_list_filters_contacts(self):
        another_plan = PlanFactory(
            title="begeleider_plan_that_should_not_be_found", created_by=self.begeleider
        )
        response = self.app.get(
            f"{self.list_url}?plan_contacts={self.contact.uuid}",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        contact_name = response.pyquery("tbody .table__item")[0].text

        self.assertEqual(
            response.context["plans"]["plan_list"],
            {self.begeleider_plan: self.contact.get_full_name()},
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(contact_name, self.contact.get_full_name())

    def test_plan_list_filters_contacts_in_multiple_plans(self):
        another_plan = PlanFactory(
            title="begeleider_plan_that_should_not_be_found", created_by=self.begeleider
        )
        another_plan.plan_contacts.add(self.begeleider, self.contact)
        response = self.app.get(
            f"{self.list_url}?plan_contacts={self.contact.uuid}",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        contact_name = response.pyquery("tbody .table__item")[0].text

        self.assertEqual(
            response.context["plans"]["plan_list"],
            {
                self.begeleider_plan: self.contact.get_full_name(),
                another_plan: self.contact.get_full_name(),
            },
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(contact_name, self.contact.get_full_name())

    def test_plan_list_filters_only_plan_contacts_no_user_contacts(self):
        self.begeleider_plan.plan_contacts.set([])
        response = self.app.get(
            f"{self.list_url}?plan_contacts={self.contact.uuid}",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")

        self.assertEqual(response.context["plans"]["plan_list"], {})
        self.assertEqual(len(rows), 1)
        self.assertIn(
            _("There are no plans with these filters."), rows[0].text_content()
        )

    @freeze_time("2022-01-01")
    def test_plan_list_filters_status_open(self):
        another_plan = PlanFactory(
            title="begeleider_plan_that_should_not_be_found",
            created_by=self.begeleider,
            end_date=date(2021, 1, 1),
        )
        self.begeleider_plan.end_date = date(2022, 1, 10)
        self.begeleider_plan.save()
        response = self.app.get(
            f"{self.list_url}?status=open",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        rendered_plan_title = response.pyquery("tbody .table__header")[0].text_content()
        contact_name = response.pyquery("tbody .table__item")[0].text

        self.assertEqual(
            response.context["plans"]["plan_list"],
            {self.begeleider_plan: self.contact.get_full_name()},
        )
        self.assertEqual(len(rows), 1)
        self.assertIn(self.begeleider_plan.title, rendered_plan_title)
        self.assertEqual(contact_name, self.contact.get_full_name())

    @freeze_time("2022-01-01")
    def test_plan_list_filters_status_closed(self):
        open_plan = PlanFactory(
            title="begeleider_plan_that_should_not_be_found",
            created_by=self.begeleider,
            end_date=date(2022, 1, 10),
        )
        self.begeleider_plan.end_date = date(2022, 1, 1)
        self.begeleider_plan.save()
        response = self.app.get(
            f"{self.list_url}?status=closed",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        rendered_plan_title = response.pyquery("tbody .table__header")[0].text_content()
        contact_name = response.pyquery("tbody .table__item")[0].text

        self.assertEqual(
            response.context["plans"]["plan_list"],
            {self.begeleider_plan: self.contact.get_full_name()},
        )
        self.assertEqual(len(rows), 1)
        self.assertIn(self.begeleider_plan.title, rendered_plan_title)
        self.assertEqual(contact_name, self.contact.get_full_name())

    @freeze_time("2022-01-01")
    def test_plans_sorting(self):
        self.begeleider_plan.delete()

        open_plan1 = PlanFactory(
            title="open - should be first",
            created_by=self.begeleider,
            end_date=date(2022, 1, 10),
            plan_contacts=[self.begeleider],
        )
        open_plan2 = PlanFactory(
            title="open - should be second",
            created_by=self.begeleider,
            end_date=date(2022, 1, 15),
            plan_contacts=[self.begeleider],
        )
        closed_plan1 = PlanFactory(
            title="closed - should be third",
            created_by=self.begeleider,
            end_date=date(2021, 12, 6),
            plan_contacts=[self.begeleider],
        )
        closed_plan2 = PlanFactory(
            title="closed - should be fourth",
            created_by=self.begeleider,
            end_date=date(2021, 11, 1),
            plan_contacts=[self.begeleider],
        )
        response = self.app.get(self.list_url, user=self.begeleider)
        rows = response.pyquery("tbody tr")
        rendered_titles = response.pyquery("tbody .table__header")

        self.assertEqual(len(rows), 4)
        self.assertIn(open_plan1.title, rendered_titles[0].text_content())
        self.assertIn(open_plan2.title, rendered_titles[1].text_content())
        self.assertIn(closed_plan1.title, rendered_titles[2].text_content())
        self.assertIn(closed_plan2.title, rendered_titles[3].text_content())

    @freeze_time("2022-01-01")
    def test_plans_sorting_with_filtering_status_open(self):
        self.begeleider_plan.delete()

        open_plan1 = PlanFactory(
            title="open - should be first",
            created_by=self.begeleider,
            end_date=date(2022, 1, 10),
            plan_contacts=[self.begeleider],
        )
        open_plan2 = PlanFactory(
            title="open - should be second",
            created_by=self.begeleider,
            end_date=date(2022, 1, 15),
            plan_contacts=[self.begeleider],
        )
        closed_plan1 = PlanFactory(
            title="closed - should be third",
            created_by=self.begeleider,
            end_date=date(2021, 12, 6),
            plan_contacts=[self.begeleider],
        )
        closed_plan2 = PlanFactory(
            title="closed - should be fourth",
            created_by=self.begeleider,
            end_date=date(2021, 11, 1),
            plan_contacts=[self.begeleider],
        )
        response = self.app.get(
            f"{self.list_url}?status=open",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        rendered_titles = response.pyquery("tbody .table__header")

        self.assertEqual(len(rows), 2)
        self.assertIn(open_plan1.title, rendered_titles[0].text_content())
        self.assertIn(open_plan2.title, rendered_titles[1].text_content())

    @freeze_time("2022-01-01")
    def test_plans_sorting_with_filtering_status_closed(self):
        self.begeleider_plan.delete()

        open_plan1 = PlanFactory(
            title="open - should not be rendered",
            created_by=self.begeleider,
            end_date=date(2022, 1, 10),
            plan_contacts=[self.begeleider],
        )
        closed_plan1 = PlanFactory(
            title="closed - should be first",
            created_by=self.begeleider,
            end_date=date(2021, 12, 6),
            plan_contacts=[self.begeleider],
        )
        closed_plan2 = PlanFactory(
            title="closed - should be second",
            created_by=self.begeleider,
            end_date=date(2021, 11, 1),
            plan_contacts=[self.begeleider],
        )
        response = self.app.get(
            f"{self.list_url}?status=closed",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        rendered_titles = response.pyquery("tbody .table__header")

        self.assertEqual(len(rows), 2)
        self.assertIn(closed_plan1.title, rendered_titles[0].text_content())
        self.assertIn(closed_plan2.title, rendered_titles[1].text_content())

    def test_plans_sorting_with_filtering_contacts(self):
        self.begeleider_plan.delete()
        another_contact = UserFactory()

        open_plan1 = PlanFactory(
            title="open - should be first",
            created_by=self.begeleider,
            end_date=date(2022, 1, 10),
            plan_contacts=[self.begeleider, self.contact],
        )
        open_plan2 = PlanFactory(
            title="open - should not be rendered",
            created_by=self.begeleider,
            end_date=date(2022, 1, 10),
            plan_contacts=[self.begeleider, another_contact],
        )
        closed_plan1 = PlanFactory(
            title="closed - should be second",
            created_by=self.begeleider,
            end_date=date(2021, 12, 6),
            plan_contacts=[self.begeleider, self.contact],
        )
        closed_plan2 = PlanFactory(
            title="closed - should be third",
            created_by=self.begeleider,
            end_date=date(2021, 11, 1),
            plan_contacts=[self.begeleider, self.contact],
        )
        response = self.app.get(
            f"{self.list_url}?plan_contacts={self.contact.uuid}",
            user=self.begeleider,
        )
        rows = response.pyquery("tbody tr")
        rendered_titles = response.pyquery("tbody .table__header")

        self.assertEqual(len(rows), 3)
        self.assertIn(open_plan1.title, rendered_titles[0].text_content())
        self.assertIn(closed_plan1.title, rendered_titles[1].text_content())
        self.assertIn(closed_plan2.title, rendered_titles[2].text_content())

    def test_search_returns_expected_plans_when_matched_with_plan_contact(self):
        self.begeleider.first_name = "expected_first_name"
        self.begeleider.last_name = "expected_last_name"
        self.begeleider.save()

        another_contact = UserFactory(
            first_name="expected_first_name", last_name="expected_last_name"
        )
        another_plan = PlanFactory(created_by=self.begeleider)
        another_plan.plan_contacts.add(self.begeleider, another_contact)

        response = self.app.get(
            f"{self.list_url}?query=expected",
            user=self.begeleider,
        )

        # response should not contain self.begeleider_plan because we don't search
        # in plan_contacts=creator
        self.assertEqual(
            response.context["plans"]["plan_list"],
            {another_plan: another_contact.get_full_name()},
        )

    def test_search_returns_expected_plans_when_matched_with_plan_title(self):
        self.begeleider_plan.title = "expected_title"
        self.begeleider_plan.save()

        another_plan = PlanFactory(
            created_by=self.begeleider, title="another_expected_title"
        )
        another_plan.plan_contacts.add(self.begeleider)

        response = self.app.get(
            f"{self.list_url}?query=expected",
            user=self.begeleider,
        )

        # response should contain both plans
        self.assertEqual(
            response.context["plans"]["plan_list"],
            {self.begeleider_plan: self.contact.get_full_name(), another_plan: ""},
        )


class NewPlanContactCounterTest(WebTest):
    def test_plan_contact_new_count(self):
        owner = UserFactory()
        plan_1 = PlanFactory(created_by=owner)
        plan_2 = PlanFactory(created_by=owner)

        user = UserFactory()

        root_url = reverse("root")
        list_url = reverse("plans:plan_list")

        # check no number shows by default
        response = self.app.get(root_url, user=user)
        links = response.pyquery(
            f".header__container > .primary-navigation a[href='{list_url}']"
        )
        self.assertEqual(len(links), 1)
        self.assertEqual(links.text(), _("Samenwerken") + " people")

        # check if the number shows up in the menu
        plan_1.plan_contacts.add(user)
        plan_2.plan_contacts.add(user)
        self.assertEqual(2, user.get_plan_contact_new_count())

        response = self.app.get(root_url, user=user)
        links = response.pyquery(
            f".header__container > .primary-navigation a[href='{list_url}']"
        )
        # second link appears
        self.assertEqual(len(links), 2)
        self.assertIn("(2)", links.text())

        # access the list page to reset
        response = self.app.get(list_url, user=user)
        links = response.pyquery(
            f".header__container > .primary-navigation a[href='{list_url}']"
        )
        self.assertEqual(len(links), 1)
        self.assertEqual(links.text(), _("Samenwerken") + " people")

        # check this doesn't appear for owner
        response = self.app.get(root_url, user=owner)
        links = response.pyquery(
            f".header__container > .primary-navigation a[href='{list_url}']"
        )
        self.assertEqual(len(links), 1)


@multi_browser()
class PlanActionStatusPlaywrightTests(ActionsPlaywrightTests):
    def setUp(self) -> None:
        super().setUp()

        # update the action to belong to our plan
        self.plan = PlanFactory(created_by=self.user)
        self.plan.plan_contacts.add(self.user)
        self.action.plan = self.plan
        self.action.save()

        # override the url to show plan detail page
        self.action_list_url = reverse(
            "plans:plan_detail", kwargs={"uuid": self.plan.uuid}
        )
