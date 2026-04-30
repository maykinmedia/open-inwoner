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


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class UserApproveContactTests(TestCase):
    def test_approve_contact_establishes_relationship(self):
        sender = UserFactory()
        receiver = UserFactory()
        sender.contacts_for_approval.add(receiver)

        result = receiver.approve_contact(sender)

        self.assertTrue(result)
        self.assertIn(sender, receiver.user_contacts.all())
        self.assertIn(receiver, sender.user_contacts.all())
        self.assertNotIn(receiver, sender.contacts_for_approval.all())

    def test_approve_contact_sends_notifications_to_both_parties(self):
        sender = UserFactory()
        receiver = UserFactory()
        sender.contacts_for_approval.add(receiver)

        mail.outbox.clear()

        receiver.approve_contact(sender)

        recipients = {m.to[0] for m in mail.outbox}
        self.assertIn(sender.email, recipients)
        self.assertIn(receiver.email, recipients)

    def test_approve_contact_returns_false_when_already_approved(self):
        sender = UserFactory()
        receiver = UserFactory()
        sender.contacts_for_approval.add(receiver)

        receiver.approve_contact(sender)
        mail.outbox.clear()

        result = receiver.approve_contact(sender)

        self.assertFalse(result)
        # No new emails should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_reject_contact_request_removes_from_pending(self):
        sender = UserFactory()
        receiver = UserFactory()
        sender.contacts_for_approval.add(receiver)

        receiver.reject_contact_request(sender)

        self.assertNotIn(receiver, sender.contacts_for_approval.all())
        self.assertNotIn(sender, receiver.user_contacts.all())
        self.assertNotIn(receiver, sender.user_contacts.all())
