import io
from unittest.mock import patch

from django.core import mail
from django.core.files.images import ImageFile
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from cms import api
from django_webtest import WebTest

from open_inwoner.accounts.models import User
from open_inwoner.utils.tests.helpers import create_image_bytes

from ..choices import ContactTypeChoices
from .factories import DigidUserFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ContactViewTests(WebTest):
    csrf_checks = False

    def setUp(self) -> None:
        self.user = UserFactory()
        self.digid_user = DigidUserFactory()

        self.contact = UserFactory()
        self.user.user_contacts.add(self.contact)
        self.login_url = reverse("login")
        self.list_url = reverse("profile:contact_list")
        self.create_url = reverse("profile:contact_create")
        self.delete_url = reverse(
            "profile:contact_delete", kwargs={"uuid": self.contact.uuid}
        )

    def test_contact_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_contact_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, self.contact.first_name)

    def test_contact_list_only_show_personal_contacts(self):
        other_user = UserFactory()
        response = self.app.get(self.list_url, user=other_user)
        self.assertNotContains(response, self.contact.first_name)

    def test_list_shows_pending_invitations(self):
        existing_user = UserFactory()
        self.user.contacts_for_approval.add(existing_user)
        response = self.app.get(self.list_url, user=self.user)

        self.assertNotContains(response, existing_user.first_name)
        self.assertContains(response, existing_user.email)

    def test_contact_filter(self):
        begeleider = UserFactory(contact_type=ContactTypeChoices.begeleider)
        self.user.user_contacts.add(begeleider)

        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, self.contact.first_name)
        self.assertContains(response, begeleider.first_name)

        form = response.forms["contact-filter"]
        form["type"] = ContactTypeChoices.begeleider
        response = form.submit()
        self.assertNotContains(response, self.contact.first_name)
        self.assertContains(response, begeleider.first_name)

    def test_contact_filter_without_any_contacts(self):
        self.contact.delete()
        response = self.app.get(self.list_url, user=self.user)
        self.assertNotContains(response, self.contact.first_name)

        form = response.forms["contact-filter"]
        form["type"] = ContactTypeChoices.contact
        response = form.submit()
        self.assertContains(
            response,
            _(
                "Er zijn geen contacten gevonden met deze filter, of u heeft nog geen contacten."
            ),
        )

    def test_messages_enabled_disabled(self):
        """Assert that `Stuur Bericht` is displayed if and only if the message page is published"""

        # case 1: no message page
        response = self.app.get(self.list_url, user=self.user)

        # self.assertNotIn(_("Stuur bericht"), response)
        self.assertNotContains(response, _("Stuur bericht"))

        # case 2: unpublished message page
        page = api.create_page(
            "Mijn Berichten",
            "cms/fullwidth.html",
            "nl",
            slug="berichten",
        )
        page.application_namespace = "inbox"
        page.save()

        response = self.app.get(self.list_url, user=self.user)

        self.assertNotContains(response, _("Stuur bericht"))

        # case 3: published message page
        page.publish("nl")
        page.save()

        response = self.app.get(self.list_url, user=self.user)

        icons = response.pyquery(".material-icons-outlined")
        message_icon = next((icon for icon in icons if icon.text == "message"), None)
        message_button_text = message_icon.tail.strip()

        self.assertEqual(_("Stuur bericht"), message_button_text)

    def test_contact_list_show_reversed(self):
        other_contact = UserFactory(first_name="reverse_contact_user_should_be_found")
        other_contact.user_contacts.add(self.user)

        response = self.app.get(self.list_url, user=self.user)
        self.assertContains(response, "reverse_contact_user_should_be_found")

    def test_contact_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")

    def test_new_user_contact_not_created_and_invite_sent(self):
        contacts_before = list(self.user.user_contacts.all())
        response = self.app.get(self.create_url, user=self.user)

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

        response = response.follow()
        self.assertContains(response, existing_user.email)
        self.assertNotContains(response, existing_user.first_name)
        self.assertEqual(existing_user, pending_invitation)

    def test_existing_user_contact_with_case_sensitive_email(self):
        existing_user = UserFactory(email="user@example.com", bsn="111111111")
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = existing_user.first_name
        form["last_name"] = existing_user.last_name
        form["email"] = "User@example.com"
        response = form.submit()

        self.assertEqual(response.status_code, 302)

        pending_invitation = self.user.contacts_for_approval.get()
        # set expiration time here?

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

        response = form.submit()

        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_user_cannot_add_themselves(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = (self.user.first_name,)
        form["last_name"] = (self.user.last_name,)
        form["email"] = (self.user.email,)
        response = form.submit(user=self.user)
        expected_errors = {"__all__": [_("You cannot add yourself as a contact.")]}

        response = form.submit()

        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_adding_contact_with_invalid_first_name_chars_fails(self):
        invalid_characters = '<>#/"\\,.:;'

        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["first_name"] = char
                form["last_name"] = "Smith"
                form["email"] = "john@smith.nl"
                response = form.submit()
                expected_errors = {
                    "first_name": [
                        _(
                            "Please make sure your input contains only valid characters "
                            "(letters, numbers, apostrophe, dash, space)."
                        )
                    ],
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_adding_contact_with_invalid_last_name_chars_fails(self):
        invalid_characters = '<>#/"\\,.:;'

        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["first_name"] = "John"
                form["last_name"] = char
                form["email"] = "john@smith.nl"
                response = form.submit()
                expected_errors = {
                    "last_name": [
                        _(
                            "Please make sure your input contains only valid characters "
                            "(letters, numbers, apostrophe, dash, space)."
                        )
                    ],
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    #
    # Contacts with duplicate emails
    #
    @override_settings(
        AUTHENTICATION_BACKENDS=["digid_eherkenning.backends.DigiDBackend"],
    )
    @patch("digid_eherkenning.backends.DigiDBackend.authenticate")
    def test_digid_contact_with_duplicate_email_success(self, m):
        m.return_value = self.digid_user

        existing_user = DigidUserFactory(
            first_name="Luke",
            last_name="Skywalker",
            bsn="111111111",
            email=self.digid_user.email,
        )

        response = self.app.get(self.create_url, user=self.user)

        form = response.forms["contact-form"]
        form["first_name"] = existing_user.first_name
        form["last_name"] = existing_user.last_name
        form["email"] = existing_user.email

        response = form.submit(user=self.digid_user)
        pending_invitation = self.digid_user.contacts_for_approval.first()

        self.assertContains(response.follow(), existing_user.email)
        self.assertEqual(existing_user, pending_invitation)

    @override_settings(
        AUTHENTICATION_BACKENDS=["digid_eherkenning.backends.DigiDBackend"],
    )
    @patch("digid_eherkenning.backends.DigiDBackend.authenticate")
    def test_digid_contact_duplicate_email_case_insensitive_success(self, m):
        m.return_value = self.digid_user

        existing_user = DigidUserFactory(
            first_name="Luke",
            last_name="Skywalker",
            bsn="111111111",
            email=self.digid_user.email,
        )

        response = self.app.get(self.create_url, user=self.user)

        form = response.forms["contact-form"]
        form["first_name"] = "lUke"
        form["last_name"] = "SkYWalKeR"
        form["email"] = existing_user.email.upper()

        response = form.submit(user=self.digid_user)
        pending_invitation = self.digid_user.contacts_for_approval.first()

        self.assertContains(response.follow(), existing_user.email)
        self.assertEqual(existing_user, pending_invitation)

    def test_email_required(self):
        response = self.app.get(self.create_url, user=self.user)
        form = response.forms["contact-form"]

        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        response = form.submit(user=self.user)
        expected_errors = {"email": ["Dit veld is vereist."]}
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
        self.assertRedirects(response, reverse("profile:contact_list"))

    def test_user_cannot_delete_other_users_contact(self):
        other_user = UserFactory()
        self.app.post(self.delete_url, user=other_user, status=404)

    def test_approve_with_existing_user(self):
        existing_user = UserFactory(email="ex@example.com")

        # Create contact from existing user
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
        self.assertRedirects(response, reverse("profile:contact_list"))

    def test_user_cannot_approve_other_users_contact(self):
        other_user = UserFactory()
        contact = UserFactory()
        self.user.contacts_for_approval.add(contact)
        url = reverse("profile:contact_approval", kwargs={"uuid": contact.uuid})
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

        # Sender contact list page
        response = self.app.get(self.list_url, user=self.user)

        self.assertContains(response, existing_user.first_name)
        self.assertContains(response, existing_user.last_name)

    def test_post_with_no_params_in_contact_approval_returns_bad_request(self):
        existing_user = UserFactory(email="ex@example.com")
        self.user.contacts_for_approval.add(existing_user)
        url = reverse("profile:contact_approval", kwargs={"uuid": self.user.uuid})
        response = self.app.post(url, user=existing_user, status=400)
        self.assertEqual(
            response.text, "contact_approve or contact_reject must be provided"
        )

    # TODO: fix
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
        self.assertEqual(
            email.subject,
            f"Goedkeuring geven op Open Inwoner Platform: {self.user.get_full_name()} wilt u toevoegen als contactpersoon",
        )
        self.assertEqual(email.to, [existing_user.email])
        invite_url = f"http://testserver{reverse('profile:contact_list')}"
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
        self.assertNotEqual(
            email.subject,
            f"Goedkeuring geven op Open Inwoner Platform: {self.user.get_full_name()} wilt u toevoegen als contactpersoon",
        )
        self.assertNotEqual(email.to, ["john@example.com"])
        invite_url = f"http://testserver{reverse('profile:contact_list')}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertNotIn(invite_url, body)

        # Email should be the one for registration, not for approval
        self.assertEqual(email.subject, "Uitnodiging voor Open Inwoner Platform")

    def test_contacts_image_is_shown_in_contact_approval_section(self):
        # prepare image
        img_bytes = create_image_bytes()
        image = ImageFile(io.BytesIO(img_bytes), name="foo.jpg")

        # update user's type and image
        existing_user = UserFactory(
            email="ex@example.com",
            contact_type=ContactTypeChoices.begeleider,
            image=image,
        )
        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.image = image
        self.user.save()
        self.user.contacts_for_approval.add(existing_user)

        # Receiver contact list page
        response = self.app.get(self.list_url, user=existing_user)
        avatar_class = response.pyquery(".avatar")

        self.assertIn(self.user.image.name, avatar_class[0].getchildren()[0].get("src"))

    def test_no_image_is_shown_in_contact_approval_section_when_no_image_set(self):
        # update user's type
        existing_user = UserFactory(
            email="ex@example.com", contact_type=ContactTypeChoices.begeleider
        )
        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.save()
        self.user.contacts_for_approval.add(existing_user)

        # Receiver contact list page
        response = self.app.get(self.list_url, user=existing_user)
        avatar_class = response.pyquery(".avatar")

        self.assertFalse(avatar_class)
