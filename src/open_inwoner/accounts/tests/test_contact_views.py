from django.core import mail
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from furl import furl

from open_inwoner.accounts.models import User

from ..choices import ContactTypeChoices
from .factories import UserFactory


class ContactViewTests(WebTest):
    csrf_checks = False

    def setUp(self) -> None:
        self.user = UserFactory()

        self.contact = UserFactory()
        self.user.user_contacts.add(self.contact)
        self.login_url = reverse("login")
        self.list_url = reverse("accounts:contact_list")
        self.create_url = reverse("accounts:contact_create")
        self.delete_url = reverse(
            "accounts:contact_delete", kwargs={"uuid": self.contact.uuid}
        )

    def test_contact_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_contact_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.contact.first_name)

    def test_contact_list_only_show_personal_contacts(self):
        other_user = UserFactory()
        response = self.app.get(self.list_url, user=other_user)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.contact.first_name)

    def test_list_shows_pending_invitations(self):
        existing_user = UserFactory()
        self.user.contacts_for_approval.add(existing_user)
        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, existing_user.first_name)

    def test_contact_filter(self):
        begeleider = UserFactory(contact_type=ContactTypeChoices.begeleider)
        self.user.user_contacts.add(begeleider)

        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.contact.first_name)
        self.assertContains(response, begeleider.first_name)

        form = response.forms["contact-filter"]
        form["type"] = ContactTypeChoices.begeleider
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.contact.first_name)
        self.assertContains(response, begeleider.first_name)

    def test_contact_filter_without_any_contacts(self):
        self.contact.delete()
        response = self.app.get(self.list_url, user=self.user)
        self.assertNotContains(response, self.contact.first_name)

        form = response.forms["contact-filter"]
        form["type"] = ContactTypeChoices.contact
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _(
                "Er zijn geen contacten gevonden met deze filter, of u heeft nog geen contacten."
            ),
        )

    def test_contact_list_show_link_to_messages(self):
        message_link = (
            furl(reverse("accounts:inbox")).add({"with": self.contact.email}).url
        )
        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, message_link)

    def test_contact_list_show_reversed(self):
        other_contact = UserFactory(first_name="reverse_contact_user_should_be_found")
        other_contact.user_contacts.add(self.user)

        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reverse_contact_user_should_be_found")

    def test_contact_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")

    def test_new_user_contact_not_created_and_invite_sent(self):
        contacts_before = list(self.user.user_contacts.all())
        response = self.app.get(self.create_url, user=self.user)
        self.assertEqual(response.status_code, 200)

        form = response.forms["contact-form"]
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["email"] = "john@smith.nl"
        response = form.submit(user=self.user)
        self.assertEqual(response.status_code, 302)

        # check that the contact was not created
        self.assertEqual(list(self.user.user_contacts.all()), contacts_before)

        # check that the invite was created
        self.assertEqual(self.user.sent_invites.count(), 1)
        invite = self.user.sent_invites.get()
        self.assertEqual(invite.inviter, self.user)

        # check that the invite was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Uitnodiging voor Open Inwoner Platform")
        self.assertEqual(email.to, [invite.invitee_email])
        invite_url = f"http://testserver{invite.get_absolute_url()}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(invite_url, body)

    def test_existing_user_contact(self):
        existing_user = UserFactory()
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = existing_user.first_name
        form["last_name"] = existing_user.last_name
        form["email"] = existing_user.email
        response = form.submit(user=self.user)
        pending_invitation = self.user.contacts_for_approval.first()

        self.assertEqual(response.status_code, 302)
        self.assertContains(response.follow(), existing_user.first_name)
        self.assertEqual(existing_user, pending_invitation)

    def test_adding_same_contact_fails(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["email"] = self.contact.email
        response = form.submit(user=self.user)
        expected_errors = {
            "__all__": [
                _(
                    "Het ingevoerde e-mailadres komt al voor in uw contactpersonen. Pas de gegevens aan en probeer het opnieuw."
                )
            ]
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_adding_contact_with_users_email_fails(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["email"] = self.user.email
        response = form.submit(user=self.user)
        expected_errors = {
            "__all__": [_("Please enter a valid email address of a contact.")]
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_adding_inactive_contact_fails(self):
        inactive_user = UserFactory(is_active=False)
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = inactive_user.first_name
        form["last_name"] = inactive_user.last_name
        form["email"] = inactive_user.email
        response = form.submit(user=self.user)
        expected_errors = {
            "__all__": [_("The user cannot be added, their account has been deleted.")]
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_email_required(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        response = form.submit(user=self.user)
        expected_errors = {"email": ["Dit veld is vereist."]}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_users_contact_is_removed(self):
        response = self.app.post(self.delete_url, user=self.user)

        new_contact_list = self.user.user_contacts.all()
        new_contact = User.objects.filter(email=self.contact.email)

        self.assertEqual(new_contact_list.count(), 0)
        self.assertTrue(new_contact.exists())
        self.assertNotContains(response.follow(), self.contact.email)

    def test_delete_contact_action_requires_login(self):
        response = self.app.post(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_delete_action_redirects_to_contact_list_page(self):
        response = self.app.post(self.delete_url, user=self.user)
        self.assertRedirects(response, reverse("accounts:contact_list"))

    def test_user_cannot_delete_other_users_contact(self):
        other_user = UserFactory()
        response = self.app.post(self.delete_url, user=other_user, status=404)

    def test_approve_with_existing_user(self):
        existing_user = UserFactory(email="ex@example.com")

        # Create a contact which addresses an existing user
        create_form = self.app.get(self.create_url, user=self.user).forms[
            "contact-form"
        ]
        create_form["first_name"] = existing_user.first_name
        create_form["last_name"] = existing_user.last_name
        create_form["email"] = existing_user.email
        create_form.submit()

        # Test approval by the existing user
        response = self.app.get(self.list_url, user=existing_user)
        self.assertContains(response, self.user.first_name)

        form = response.forms["approval_form"]
        response = form.submit("contact_approve")

        self.assertFalse(self.user.contacts_for_approval.exists())
        self.assertIn(existing_user, self.user.user_contacts.all())
        self.assertIn(self.user, existing_user.user_contacts.all())

    def test_reject_with_existing_user(self):
        existing_user = UserFactory(email="ex@example.com")

        # Create a contact which addresses an existing user
        create_form = self.app.get(self.create_url, user=self.user).forms[
            "contact-form"
        ]
        create_form["first_name"] = existing_user.first_name
        create_form["last_name"] = existing_user.last_name
        create_form["email"] = existing_user.email
        create_form.submit()

        # Test approval by the existing user
        response = self.app.get(self.list_url, user=existing_user)
        self.assertContains(response, self.user.first_name)

        form = response.forms["approval_form"]
        response = form.submit("contact_reject")

        self.assertFalse(self.user.contacts_for_approval.exists())
        self.assertNotIn(existing_user, self.user.user_contacts.all())
        self.assertNotIn(self.user, existing_user.user_contacts.all())

    def test_approve_action_redirects_to_contact_list_page(self):
        existing_user = UserFactory(email="ex@example.com")
        self.user.contacts_for_approval.add(existing_user)

        response = self.app.get(self.list_url, user=existing_user)
        form = response.forms["approval_form"]
        response = form.submit("contact_approve")
        self.assertRedirects(response, reverse("accounts:contact_list"))

    def test_user_cannot_approve_other_users_contact(self):
        other_user = UserFactory()
        contact = UserFactory()
        self.user.contacts_for_approval.add(contact)
        url = reverse("accounts:contact_approval", kwargs={"uuid": contact.uuid})
        response = self.app.post(url, user=other_user, status=404)

    def test_pending_approval_shows_only_email_in_creator_page(self):
        existing_user = UserFactory(email="uu@example.com", phonenumber="06988989898")
        self.user.contacts_for_approval.add(existing_user)

        response = self.app.get(self.list_url, user=self.user)

        self.assertContains(response, existing_user.email)
        self.assertNotContains(response, existing_user.first_name)
        self.assertNotContains(response, existing_user.last_name)
        self.assertNotContains(response, existing_user.phonenumber)

    def test_accepted_contact_appears_in_both_contact_lists(self):
        existing_user = UserFactory(email="ex@example.com")
        self.user.contacts_for_approval.add(existing_user)

        # Receiver contact list page
        response = self.app.get(self.list_url, user=existing_user)
        self.assertContains(response, self.user.first_name)

        form = response.forms["approval_form"]
        response = form.submit("contact_approve").follow()

        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)
        self.assertContains(response, self.user.email)

        # Sender contact list page
        response = self.app.get(self.list_url, user=self.user)

        self.assertContains(response, existing_user.first_name)
        self.assertContains(response, existing_user.last_name)
        self.assertContains(response, existing_user.email)

    def test_post_with_no_params_in_contact_approval_returns_bad_request(self):
        existing_user = UserFactory(email="ex@example.com")
        self.user.contacts_for_approval.add(existing_user)
        url = reverse("accounts:contact_approval", kwargs={"uuid": self.user.uuid})
        response = self.app.post(url, user=existing_user, status=400)
        self.assertEqual(
            response.text, "contact_approve or contact_reject must be provided"
        )

    def test_notification_email_for_approval_is_sent(self):
        existing_user = UserFactory(email="ex@example.com")

        # Create a contact which addresses an existing user
        create_form = self.app.get(self.create_url, user=self.user).forms[
            "contact-form"
        ]
        create_form["first_name"] = existing_user.first_name
        create_form["last_name"] = existing_user.last_name
        create_form["email"] = existing_user.email
        create_form.submit()

        # check that the notification email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Approval for Open Inwoner Platform")
        self.assertEqual(email.to, [existing_user.email])
        invite_url = f"http://testserver{reverse('login')}?next={reverse('accounts:contact_list')}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(invite_url, body)

    def test_notification_email_for_approval_is_not_sent_when_new_user(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["email"] = "john@example.nl"
        response = form.submit()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertNotEqual(email.subject, "Approval for Open Inwoner Platform")
        self.assertNotEqual(email.to, ["john@example.com"])
        invite_url = f"http://testserver{reverse('login')}?next={reverse('accounts:contact_list')}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertNotIn(invite_url, body)

        # Email should be the one for registration, not for approval
        self.assertEqual(email.subject, "Uitnodiging voor Open Inwoner Platform")
