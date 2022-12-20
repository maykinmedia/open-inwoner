from unittest import skip

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse, reverse_lazy

from django_webtest import WebTest
from privates.test import temp_private_root
from selenium.webdriver.common.by import By

from open_inwoner.utils.tests.selenium import ChromeSeleniumMixin, FirefoxSeleniumMixin

from ..models import Message
from .factories import MessageFactory, UserFactory


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

        self.url = reverse("accounts:inbox")
        self.contact1_url = reverse(
            "accounts:inbox", kwargs={"uuid": self.contact1.uuid}
        )

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
            reverse("accounts:inbox", kwargs={"uuid": other_user.uuid}),
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


class BaseInboxPageSeleniumTests:
    options = None
    driver = None
    selenium = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium.implicitly_wait(10)

    def setUp(self):
        self.user = UserFactory.create()
        self.contact_1 = UserFactory.create(
            first_name="user", last_name="1", email="user1@example.com"
        )
        self.contact_2 = UserFactory.create(
            first_name="user", last_name="2", email="user2@example.com"
        )
        self.user.user_contacts.add(self.contact_1)
        self.user.user_contacts.add(self.contact_2)
        MessageFactory.create(sender=self.user, receiver=self.contact_1)
        MessageFactory.create(receiver=self.user, sender=self.contact_2)

    def test_async_selector(self):
        self.given_i_am_logged_in()
        self.when_i_navigate_to_page()

        # Send message.
        message_count = len(self.selenium.find_elements(By.CSS_SELECTOR, ".message"))
        content_textarea = self.selenium.find_element(By.NAME, "content")
        content_textarea.send_keys("Lorem ipsum dolor sit amet.")
        form = self.selenium.find_element(By.CSS_SELECTOR, "#message-form")
        form.submit()

        # Assert message.
        selector = f".messages__list-item:nth-child({message_count + 1}) .message"
        message = self.selenium.find_element(By.CSS_SELECTOR, selector)
        self.assertIn("Lorem ipsum dolor sit amet.", message.text)

        # assert async.
        url = f"{self.live_server_url}{reverse_lazy('accounts:inbox')}?redirected=True"
        self.assertEqual(url, self.selenium.current_url)
        self.assertNotIn("#messages-last", self.selenium.current_url)

    def test_polling(self):
        self.given_i_am_logged_in()
        self.when_i_navigate_to_page()

        # Create message.
        initial_message_count = len(
            self.selenium.find_elements(By.CSS_SELECTOR, ".message")
        )
        initial_selector = (
            f".messages__list-item:nth-child({initial_message_count}) .message"
        )
        initial_message = self.selenium.find_element(By.CSS_SELECTOR, initial_selector)
        initial_text = initial_message.text

        Message.objects.create(
            receiver=self.user,
            sender=self.contact_2,
            content="Lorem ipsum dolor sit amet.",
        )

        # Assert message.
        new_selector = (
            f".messages__list-item:nth-child({initial_message_count + 1}) .message"
        )
        new_message = self.selenium.find_element(By.CSS_SELECTOR, new_selector)
        self.assertIn("Lorem ipsum dolor sit amet.", new_message.text)

        # Previous message.
        previous_selector = (
            f".messages__list-item:nth-child({initial_message_count}) .message"
        )
        previous_message = self.selenium.find_element(
            By.CSS_SELECTOR, previous_selector
        )
        self.assertEqual(initial_text, previous_message.text)

        # assert async.
        url = f"{self.live_server_url}{reverse_lazy('accounts:inbox')}?redirected=True"
        self.assertEqual(url, self.selenium.current_url)
        self.assertNotIn("#messages-last", self.selenium.current_url)

    def given_i_am_logged_in(self):
        self.force_login(self.user)

    def when_i_navigate_to_page(self):
        self.selenium.get(
            "%s%s" % (self.live_server_url, reverse_lazy("accounts:inbox"))
        )


@skip("skipped for now because of random CI failures, ref Taiga #963")
class InboxPageFirefoxSeleniumTests(
    FirefoxSeleniumMixin, BaseInboxPageSeleniumTests, StaticLiveServerTestCase
):
    pass


@skip("skipped for now because of random CI failures, ref Taiga #963")
class InboxPageChromeSeleniumTests(
    ChromeSeleniumMixin, BaseInboxPageSeleniumTests, StaticLiveServerTestCase
):
    pass
