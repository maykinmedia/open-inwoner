from django.core import mail
from django.urls import reverse_lazy

from django_webtest import WebTest
from furl import furl

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

        form = response.forms[1]
        form["content"] = "some msg"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "some msg")
        self.assertEqual(last_message.sender, self.me)
        self.assertEqual(last_message.receiver, self.user1)

        # check that the email was send
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(
            email.subject,
            f"New message from {self.me.get_full_name()} at Open Inwoner Platform",
        )
        self.assertEqual(email.to, [self.user1.email])
        inbox_url = f"http://testserver{furl(self.url).add({'with':self.me.email}).url}"
        body = email.alternatives[0][0]  # html version of the email body
        self.assertIn(inbox_url, body)
