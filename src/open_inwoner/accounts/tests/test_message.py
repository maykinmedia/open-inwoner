from django.test import TestCase

from freezegun import freeze_time

from .factories import MessageFactory, UserFactory


class MessageTest(TestCase):
    def setUp(self):
        self.sender = UserFactory.create(
            first_name="Person", last_name="A", email="person-a@example.com"
        )
        self.receiver = UserFactory.create(
            first_name="Person", last_name="B", email="person-b@example.com"
        )

    def test_create(self):
        MessageFactory.create()

    @freeze_time("2021-12-21")
    def test_str(self):
        message = MessageFactory(sender=self.sender, receiver=self.receiver)
        self.assertEqual(
            str(message),
            f"From: {self.sender}, To: {self.receiver} (2021-12-21)",
        )
        message.delete()
