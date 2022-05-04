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
