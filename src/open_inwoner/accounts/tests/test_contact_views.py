from django.core import mail
from django.urls import reverse

from django_webtest import WebTest

from .factories import ContactFactory, UserFactory


class ContactViewTests(WebTest):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.contact = ContactFactory(
            first_name="contact_that_should_be_found", created_by=self.user
        )

        self.login_url = reverse("login")
        self.list_url = reverse("accounts:contact_list")
        self.edit_url = reverse(
            "accounts:contact_edit", kwargs={"uuid": self.contact.uuid}
        )
        self.create_url = reverse("accounts:contact_create")

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

    def test_contact_edit_login_required(self):
        response = self.app.get(self.edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.edit_url}")

    def test_contact_edit(self):
        response = self.app.get(self.edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.contact.first_name)

    def test_contact_edit_not_your_contact(self):
        other_user = UserFactory()
        response = self.app.get(self.edit_url, user=other_user, status=404)

    def test_contact_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")

    def test_contact_create_send_invite(self):
        contacts_before = self.user.contacts.count()
        response = self.app.get(self.create_url, user=self.user)
        self.assertEqual(response.status_code, 200)

        form = response.forms[1]
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["email"] = "john@smith.nl"

        response = form.submit(user=self.user)

        self.assertEqual(response.status_code, 302)

        # check that the contact was created
        self.assertEqual(self.user.contacts.count(), contacts_before + 1)
        contact = self.user.contacts.order_by("-pk").first()
        self.assertEqual(contact.first_name, "John")
        self.assertEqual(contact.last_name, "Smith")
        self.assertEqual(contact.email, "john@smith.nl")

        # check that the contact was created
        contact_user = contact.contact_user
        self.assertIsNotNone(contact_user)
        self.assertEqual(contact_user.email, "john@smith.nl")
        self.assertFalse(contact_user.is_active)

        # check that the invite was created
        self.assertEqual(contact.invites.count(), 1)
        invite = contact.invites.get()
        self.assertEqual(invite.inviter, self.user)
        self.assertEqual(invite.invitee, contact_user)

        # check that the invite was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Invitation for Open Inwoner Platform")
        self.assertEqual(email.to, [contact_user.email])
        invite_url = f"http://testserver{invite.get_absolute_url()}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(invite_url, body)
