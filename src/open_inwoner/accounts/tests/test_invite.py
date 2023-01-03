from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest

from .factories import InviteFactory, UserFactory


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

    def test_invite_automatically_accepted_when_loggedin(self):
        user = UserFactory()
        invite = InviteFactory.create(invitee=user, invitee_email=user.email)
        url = invite.get_absolute_url()

        self.assertFalse(invite.accepted)

        response = self.app.get(url, user=user)

        form = response.forms["invite-form"]
        response = form.submit(status=404)

        invite.refresh_from_db()

        self.assertTrue(invite.accepted)

    def test_invite_not_accepted_when_loggedin_with_different_account(self):
        user = UserFactory()
        other_user = UserFactory()
        invite = InviteFactory.create(invitee=user, invitee_email=user.email)
        url = invite.get_absolute_url()

        self.assertFalse(invite.accepted)

        response = self.app.get(url, user=other_user, status=404)

        invite.refresh_from_db()

        self.assertFalse(invite.accepted)

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
