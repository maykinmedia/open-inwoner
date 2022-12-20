from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .factories import MessageFactory, UserFactory


class NotifyComandTests(TestCase):
    def test_notify_about_received_message(self):
        user, sender1, sender2 = UserFactory.create_batch(3)
        message1 = MessageFactory.create(receiver=user, sender=sender1)
        messages2 = MessageFactory.create_batch(2, receiver=user, sender=sender2)
        messages = [message1] + messages2
        for message in messages:
            self.assertFalse(message.sent)

        call_command("notify_about_messages")

        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertEqual(sent_mail.subject, "New messages at Open Inwoner Platform")
        self.assertEqual(sent_mail.to, [user.email])
        self.assertIn("You've received 3 new messages from 2 users", sent_mail.body)
        self.assertIn(reverse("accounts:inbox"), html_body)

        for message in messages:
            message.refresh_from_db()
            self.assertTrue(message.sent)

    def test_seen_message(self):
        user = UserFactory.create()

        message = MessageFactory.create(receiver=user, seen=True)

        call_command("notify_about_messages")

        self.assertEqual(len(mail.outbox), 0)

        message.refresh_from_db()
        self.assertFalse(message.sent)

    def test_sent_message(self):
        user = UserFactory.create()

        MessageFactory.create(receiver=user, sent=True)

        call_command("notify_about_messages")

        self.assertEqual(len(mail.outbox), 0)

    def test_notify_several_users(self):
        user1, user2, sender = sorted(
            UserFactory.create_batch(3, first_name="John", last_name="Smith"),
            key=lambda x: x.email,
        )
        messages1 = MessageFactory.create_batch(3, receiver=user1, sender=sender)
        messages2 = MessageFactory.create_batch(2, receiver=user2, sender=sender)
        messages = messages1 + messages2
        for message in messages:
            self.assertFalse(message.sent)

        call_command("notify_about_messages")

        self.assertEqual(len(mail.outbox), 2)

        email1, email2 = sorted(mail.outbox, key=lambda x: x.to, reverse=True)
        for email in [email1, email2]:
            self.assertEqual(email.subject, "New messages at Open Inwoner Platform")
            html_body = email.alternatives[0][0]
            self.assertIn(reverse("accounts:inbox"), html_body)

        self.assertEqual(email1.to, [user2.email])
        self.assertIn("You've received 2 new messages from 1 users", email1.body)
        self.assertEqual(email2.to, [user1.email])
        self.assertIn("You've received 3 new messages from 1 users", email2.body)
