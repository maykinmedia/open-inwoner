from django.urls import reverse_lazy

from django_webtest import WebTest
from privates.test import temp_private_root

from ..models import Message
from .factories import ContactFactory, MessageFactory, UserFactory


class InboxPageTests(WebTest):
    url = reverse_lazy("accounts:inbox")

    def setUp(self) -> None:
        super().setUp()

        self.me = UserFactory.create()
        self.user1, self.user2 = UserFactory.create_batch(2)
        ContactFactory.create(
            created_by=self.me, contact_user=self.user1, email=self.user1.email
        )
        ContactFactory.create(
            created_by=self.me, contact_user=self.user2, email=self.user2.email
        )
        self.message1 = MessageFactory.create(sender=self.me, receiver=self.user1)
        self.message2 = MessageFactory.create(receiver=self.me, sender=self.user2)

        self.app.set_user(self.me)

    def test_show_last_conversation_without_other_user(self):
        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message2.id)

    def test_show_conversation_with_user_specified(self):
        response = self.app.get(self.url, {"with": self.user1.email})

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message1.id)

    def test_send_message(self):
        response = self.app.get(self.url, {"with": self.user1.email})
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        form["content"] = "some msg"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "some msg")
        self.assertEqual(last_message.sender, self.me)
        self.assertEqual(last_message.receiver, self.user1)

    @temp_private_root()
    def test_send_file(self):
        response = self.app.get(self.url, {"with": self.user1.email})
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        form["file"] = ("file.txt", b"test content")

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "")
        self.assertEqual(last_message.sender, self.me)
        self.assertEqual(last_message.receiver, self.user1)

        file = last_message.file
        self.assertEqual(file.name, "file.txt")
        self.assertEqual(file.read(), b"test content")

    def test_send_empty_message(self):
        response = self.app.get(self.url, {"with": self.user1.email})
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"][0],
            "Of een bericht of een bestand dient te zijn ingevuld",
        )

    def test_mark_messages_as_seen(self):
        other_user = UserFactory.create()
        ContactFactory.create(
            created_by=self.me, contact_user=self.user1, email=self.user1.email
        )
        message_received = MessageFactory.create(receiver=self.me, sender=other_user)
        message_sent = MessageFactory.create(sender=self.me, receiver=other_user)

        for message in [message_sent, message_received]:
            self.assertFalse(message.seen)

        response = self.app.get(self.url, {"with": other_user.email})
        self.assertEqual(response.status_code, 200)

        for message in [message_sent, message_received]:
            message.refresh_from_db()

        self.assertFalse(message_sent.seen)
        self.assertTrue(message_received.seen)
