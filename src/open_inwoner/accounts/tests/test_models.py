from django.core import mail
from django.test import TestCase, override_settings

from .factories import InviteFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class InviteAcceptTests(TestCase):
    def test_accept_establishes_contact_relationship(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(inviter=inviter, invitee=invitee)

        result = invite.accept(invitee)

        self.assertTrue(result)
        self.assertIn(invitee, inviter.user_contacts.all())
        self.assertIn(inviter, invitee.user_contacts.all())

    def test_accept_returns_false_when_already_accepted(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(inviter=inviter, invitee=invitee)
        invite.accept(invitee)

        result = invite.accept(invitee)

        self.assertFalse(result)

    def test_send_accepted_emails_sends_to_both_parties(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(inviter=inviter, invitee=invitee)
        invite.accept(invitee)

        recipients = {m.to[0] for m in mail.outbox}
        self.assertIn(inviter.email, recipients)
        self.assertIn(invitee.email, recipients)

    def test_accepted_emails_not_sent_twice_on_double_accept(self):
        inviter = UserFactory()
        invitee = UserFactory()
        invite = InviteFactory.create(inviter=inviter, invitee=invitee)

        invite.accept(invitee)
        count_after_first = len(mail.outbox)

        invite.accept(invitee)

        self.assertEqual(len(mail.outbox), count_after_first)
