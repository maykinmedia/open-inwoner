from unittest import skip

from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from playwright.sync_api import expect
from privates.test import temp_private_root

from open_inwoner.utils.tests.playwright import (
    PlaywrightSyncLiveServerTestCase,
    multi_browser,
)

from ..models import Message
from .factories import DigidUserFactory, MessageFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class InboxPageTests(WebTest):
    def setUp(self) -> None:
        super().setUp()

        self.user = UserFactory.create(
            email="user@exampel.com", first_name="User", last_name="U"
        )
        self.contact1 = UserFactory.create(
            email="contact1@exampel.com", first_name="Contact1", last_name="U"
        )
        self.contact2 = UserFactory.create(
            email="contact2@exampel.com", first_name="Contact2", last_name="U"
        )
        self.user.user_contacts.add(self.contact1)
        self.user.user_contacts.add(self.contact2)
        self.message1 = MessageFactory.create(
            content="from user to contact1", sender=self.user, receiver=self.contact1
        )
        self.message2 = MessageFactory.create(
            content="from contact2 to user", receiver=self.user, sender=self.contact2
        )

        self.app.set_user(self.user)

        self.url = reverse("inbox:index")
        self.contact1_url = reverse("inbox:index", kwargs={"uuid": self.contact1.uuid})

    def test_user_contacts_are_symetrical(self):
        self.assertIn(self.contact1, self.user.user_contacts.all())
        self.assertIn(self.user, self.contact1.user_contacts.all())

    def test_show_last_conversation_without_other_user(self):
        response = self.app.get(self.url, auto_follow=True)

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message2.id)

    def test_show_conversation_with_user_specified(self):
        response = self.app.get(self.contact1_url, auto_follow=True)

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message1.id)

    def test_send_message(self):
        response = self.app.get(self.contact1_url, auto_follow=True)
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        form["content"] = "some msg"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "some msg")
        self.assertEqual(last_message.sender, self.user)
        self.assertEqual(last_message.receiver, self.contact1)

    @temp_private_root()
    def test_send_file(self):
        response = self.app.get(self.contact1_url, auto_follow=True)
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        form["file"] = ("file.txt", b"test content")

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "")
        self.assertEqual(last_message.sender, self.user)
        self.assertEqual(last_message.receiver, self.contact1)

        file = last_message.file
        self.assertEqual(file.name, "file.txt")
        self.assertEqual(file.read(), b"test content")

    def test_send_empty_message(self):
        response = self.app.get(self.contact1_url, auto_follow=True)
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"][0],
            "Of een bericht of een bestand moet ingevuld zijn",
        )

    def test_mark_messages_as_seen(self):
        other_user = UserFactory.create()
        message_received = MessageFactory.create(receiver=self.user, sender=other_user)
        message_sent = MessageFactory.create(sender=self.user, receiver=other_user)

        for message in [message_sent, message_received]:
            self.assertFalse(message.seen)

        response = self.app.get(
            reverse("inbox:index", kwargs={"uuid": other_user.uuid}),
            auto_follow=True,
        )
        self.assertEqual(response.status_code, 200)

        for message in [message_sent, message_received]:
            message.refresh_from_db()

        self.assertFalse(message_sent.seen)
        self.assertTrue(message_received.seen)

    def test_reply_message(self):
        # test if a contact can reply if they were added to 'self.user.user_contacts' (eg: symmetrical)
        self.app.set_user(self.contact1)
        response = self.app.get(self.url, auto_follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.message1.content)

        form = response.forms["message-form"]
        form["content"] = "some msg"

        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "some msg")

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "some msg")
        self.assertEqual(last_message.sender, self.contact1)
        self.assertEqual(last_message.receiver, self.user)

    def test_no_messages(self):
        Message.objects.all().delete()

        response = self.app.get(self.url, auto_follow=True)
        self.assertEqual(response.status_code, 200)
        # no form
        self.assertFalse(response.pyquery("form#message-form"))

    def test_no_contacts(self):
        self.contact1.delete()
        self.contact2.delete()

        response = self.app.get(self.url, auto_follow=True)
        self.assertEqual(response.status_code, 200)
        # no form
        self.assertFalse(response.pyquery("form#message-form"))


@multi_browser()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class InboxPagePlaywrightTests(PlaywrightSyncLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = DigidUserFactory.create()
        # let's reuse the login storage_state
        cls.user_login_state = cls.get_user_bsn_login_state(cls.user)

    def setUp(self):
        super().setUp()

        self.contact_1 = UserFactory.create(
            first_name="user", last_name="1", email="user1@example.com"
        )
        self.contact_2 = UserFactory.create(
            first_name="user", last_name="2", email="user2@example.com"
        )
        self.user.user_contacts.add(self.contact_1)
        self.user.user_contacts.add(self.contact_2)
        self.message_1 = MessageFactory.create(
            content="Message#1 content", sender=self.user, receiver=self.contact_1
        )
        self.message_2 = MessageFactory.create(
            content="Message#2 content",
            receiver=self.user,
            sender=self.contact_2,
        )
        self.contact_1_conversation_url = self.live_reverse(
            "inbox:index",
            kwargs={"uuid": self.contact_1.uuid},
        )

    @skip("re-implement on playwright after re-enabling")
    def test_async_selector(self):
        """
        make sure to test re-hydration and if emoji and file components work after a submit
        """

    def test_polling(self):
        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()
        page.goto(self.contact_1_conversation_url)

        messages = page.locator(".messages__list-item")

        # show conversation with contact_1
        expect(messages.filter(has_text=self.message_1.content)).to_have_count(1)
        expect(messages.filter(has_text=self.message_2.content)).to_have_count(0)

        new_message = Message.objects.create(
            receiver=self.user,
            sender=self.contact_1,
            content="Message#3 content",
        )
        # wait for poll to trigger
        messages.filter(has_text=new_message.content).wait_for()
