from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from typeguard import check_type

from .factories import MessageFactory, UserFactory
from ...components.types.messagetype import MessageKind, MessageType


class MessageTest(TestCase):
    def setUp(self):
        self.sender = UserFactory.create(
            first_name="Person", last_name="A", email="person-a@example.com"
        )
        self.receiver = UserFactory.create(
            first_name="Person", last_name="B", email="person-b@example.com"
        )

    def tearDown(self):
        self.sender.delete()
        self.receiver.delete()

    def test_create(self):
        MessageFactory.create()

    @freeze_time("2021-12-21")
    def test_str(self):
        message = MessageFactory(sender=self.sender, receiver=self.receiver)
        self.assertEqual(
            str(message),
            "From: person-a@example.com, To: person-b@example.com (2021-12-21)",
        )
        message.delete()

    @freeze_time("2021-12-21 17:22:57")
    def test_as_message_type(self):
        message = MessageFactory(
            sender=self.sender, receiver=self.receiver, content="Lorem ipsum."
        )
        message_type = message.as_message_type()

        self.assertEqual(
            message_type,
            {
                "sender": {
                    "sender_id": f"sender-{self.sender.pk}",
                    "display_name": "person-a@example.com",
                },
                "message_id": f"message-{message.pk}",
                "sent_datetime": timezone.now(),
                "kind": MessageKind.TEXT,
                "data": "Lorem ipsum.",
            },
        )

        check_type("message_type", message_type, MessageType)
