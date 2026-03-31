from datetime import timedelta

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest

from open_inwoner.configurations.models import SiteConfiguration

from .factories import InviteFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class InvitePageTests(WebTest):
    def setUp(self):
        super().setUp()

        self.invitee = UserFactory(is_active=False)

    def test_accept_invite(self):
        invite = InviteFactory.create(invitee=self.invitee)
        url = invite.get_absolute_url()

        response = self.app.get(url)

        self.assertEqual(response.status_code, 200)

        form = response.forms["invite-form"]
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('django_registration_register')}?invite={invite.key}",
        )

    def test_accept_invite_expired(self):
        invite = InviteFactory.create(invitee=self.invitee)
        invite.created_on = timezone.now() - timedelta(days=30)
        invite.save()
        url = invite.get_absolute_url()

        response = self.app.get(url, status=404)

        self.assertEqual(response.status_code, 404)

    def test_invite_not_automatically_accepted_when_not_loggedin(self):
        user = UserFactory()
        invite = InviteFactory.create(invitee=user, invitee_email=user.email)
        url = invite.get_absolute_url()

        self.assertFalse(invite.accepted)

        response = self.app.get(url)

        invite.refresh_from_db()

        self.assertFalse(invite.accepted)

    def test_invite_automatically_accepted_when_loggedin(self):
        user = UserFactory()
        invite = InviteFactory.create(invitee=user, invitee_email=user.email)
        url = invite.get_absolute_url()

        self.assertFalse(invite.accepted)

        response = self.app.get(url, user=user)

        invite.refresh_from_db()

        self.assertTrue(invite.accepted)

    def test_contact_relationship_is_automatically_added_when_logged_in(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(inviter=inviter, invitee=invitee)
        url = invite.get_absolute_url()
        response = self.app.get(url, user=invitee)

        self.assertEqual(inviter.user_contacts.get(), invitee)
        self.assertEqual(invitee.user_contacts.get(), inviter)

    def test_invite_url_is_saved_to_session_after_acceptance(self):
        invite = InviteFactory()
        url = invite.get_absolute_url()

        response = self.app.get(url)

        form = response.forms["invite-form"]
        response = form.submit()

        self.assertEqual(
            self.app.session["invite_url"],
            f"{reverse('django_registration_register')}?invite={invite.key}",
        )

    def test_accepted_emails_sent_to_both_users_when_logged_in(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(inviter=inviter, invitee=invitee)
        url = invite.get_absolute_url()

        self.app.get(url, user=invitee)

        recipients = {m.to[0] for m in mail.outbox}
        self.assertIn(inviter.email, recipients)
        self.assertIn(invitee.email, recipients)

    def test_accepted_emails_sent_to_both_users_via_registration(self):
        config = SiteConfiguration.get_solo()
        config.login_allow_registration = True
        config.save()

        inviter = UserFactory()
        invite = InviteFactory.create(inviter=inviter)
        url = f"{reverse('django_registration_register')}?invite={invite.key}"

        page = self.app.get(url)
        form = page.forms["registration-form"]
        form["email"] = invite.invitee_email
        form["first_name"] = invite.invitee_first_name
        form["last_name"] = invite.invitee_last_name
        form["password1"] = "SomePassword1!"
        form["password2"] = "SomePassword1!"
        form.submit()

        recipients = {m.to[0] for m in mail.outbox}
        self.assertIn(inviter.email, recipients)
        self.assertIn(invite.invitee_email, recipients)

    def test_accepted_emails_sent_to_both_users_via_necessary_fields(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(
            inviter=inviter,
            invitee=invitee,
            invitee_email=invitee.email,
        )
        url = f"{reverse('profile:registration_necessary')}?invite={invite.key}"

        page = self.app.get(url, user=invitee)
        form = page.forms["necessary-form"]
        form["first_name"] = invitee.first_name
        form["last_name"] = invitee.last_name
        form["email"] = invitee.email
        form.submit()

        recipients = {m.to[0] for m in mail.outbox}
        self.assertIn(inviter.email, recipients)
        self.assertIn(invitee.email, recipients)
