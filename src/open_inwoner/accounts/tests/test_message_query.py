from django.test import TestCase

from ..models import Message
from .factories import MessageFactory, UserFactory


class ConversationTests(TestCase):
    """test MessageQuerySet.get_conversations_for_user"""

    def setUp(self) -> None:
        super().setUp()

        self.user = UserFactory.create()

    def test_no_other_user(self):
        conversations = Message.objects.get_conversations_for_user(self.user)

        self.assertEqual(conversations.count(), 0)

    def test_1_other_user_received_last(self):
        other = UserFactory.create()
        sent_message = MessageFactory.create(sender=self.user, receiver=other)
        received_message = MessageFactory.create(receiver=self.user, sender=other)

        conversations = Message.objects.get_conversations_for_user(self.user)

        self.assertEqual(conversations.count(), 1)

        message = conversations[0]
        self.assertEqual(message, received_message)
        self.assertEqual(message.other_user_uuid, other.uuid)
        self.assertEqual(message.other_user_first_name, other.first_name)
        self.assertEqual(message.other_user_last_name, other.last_name)

    def test_1_other_user_sent_last(self):
        other = UserFactory.create()
        received_message = MessageFactory.create(receiver=self.user, sender=other)
        sent_message = MessageFactory.create(sender=self.user, receiver=other)

        conversations = Message.objects.get_conversations_for_user(self.user)

        self.assertEqual(conversations.count(), 1)

        message = conversations[0]
        self.assertEqual(message, sent_message)
        self.assertEqual(message.other_user_uuid, other.uuid)
        self.assertEqual(message.other_user_first_name, other.first_name)
        self.assertEqual(message.other_user_last_name, other.last_name)

    def test_2_other_users(self):
        sender, receiver = UserFactory.create_batch(2)
        sender_message1, sender_message2 = MessageFactory.create_batch(
            2, receiver=self.user, sender=sender
        )
        receiver_message1, receiver_message2 = MessageFactory.create_batch(
            2, sender=self.user, receiver=receiver
        )

        conversations = Message.objects.get_conversations_for_user(self.user)

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(conversations[0], receiver_message2)
        self.assertEqual(conversations[1], sender_message2)
