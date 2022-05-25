from django.core import mail
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from furl import furl

from open_inwoner.accounts.models import Contact

from ..choices import ContactTypeChoices
from .factories import ContactFactory, UserFactory


class ContactViewTests(WebTest):
    csrf_checks = False

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

    def test_contact_filter(self):
        begeleider = ContactFactory(
            contact_user__contact_type=ContactTypeChoices.begeleider,
            created_by=self.user,
        )
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

    def test_contact_filter_when_no_user_is_connected(self):
        contact = ContactFactory(created_by=self.user, email=None, contact_user=None)
        begeleider = ContactFactory(
            contact_user__contact_type=ContactTypeChoices.begeleider,
            created_by=self.user,
        )
        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, self.contact.first_name)
        self.assertContains(response, contact.first_name)

        form = response.forms["contact-filter"]
        form["type"] = ContactTypeChoices.contact
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.contact.first_name)
        self.assertContains(response, contact.first_name)
        self.assertNotContains(response, begeleider.first_name)

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
        other_user = UserFactory()
        contact = ContactFactory.create(created_by=self.user, contact_user=other_user)
        contacts = Contact.objects.get_extended_contacts_for_user(self.user)
        extended_contact = contacts.get(id=contact.id)
        message_link = (
            furl(reverse("accounts:inbox"))
            .add({"with": extended_contact.other_user_email})
            .url
        )
        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, message_link)

    def test_contact_list_show_reversed(self):
        ContactFactory.create(
            contact_user=self.user,
            created_by__first_name="reverse_contact_user_should_be_found",
        )
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reverse_contact_user_should_be_found")

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

        form = response.forms["contact-form"]
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

        # check that the contact user was not created
        self.assertIsNone(contact.contact_user)

        # check that the invite was created
        self.assertEqual(contact.invites.count(), 1)
        invite = contact.invites.get()
        self.assertEqual(invite.inviter, self.user)
        self.assertEqual(invite.invitee_email, contact.email)

        # check that the invite was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Uitnodiging voor Open Inwoner Platform")
        self.assertEqual(email.to, [invite.invitee_email])
        invite_url = f"http://testserver{invite.get_absolute_url()}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(invite_url, body)

    def test_multiple_contact_create_without_providing_email(self):
        ContactFactory(email=None)
        response = self.app.get(self.create_url, user=self.user)
        self.assertEqual(response.status_code, 200)

        form = response.forms["contact-form"]
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        response = form.submit(user=self.user)
        contacts_without_email = Contact.objects.filter(email__isnull=True)

        self.assertEqual(contacts_without_email.count(), 2)

    def test_users_contact_is_deleted(self):
        self.app.post(self.delete_url, user=self.user)

        new_contact_list = Contact.objects.all()
        self.assertEquals(new_contact_list.count(), 0)

    def test_delete_contact_action_requires_login(self):
        response = self.app.post(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_delete_action_redirects_to_contact_list_page(self):
        response = self.app.post(self.delete_url, user=self.user)
        self.assertRedirects(response, reverse("accounts:contact_list"))

    def test_user_cannot_delete_other_users_contact(self):
        other_user = UserFactory()
        response = self.app.post(self.delete_url, user=other_user, status=404)
