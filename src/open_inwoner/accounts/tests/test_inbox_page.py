from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse_lazy

from django_webtest import WebTest
from privates.test import temp_private_root
from selenium.webdriver.common.by import By

from open_inwoner.utils.tests.selenium import ChromeSeleniumTests, FirefoxSeleniumTests

from ..models import Message
from .factories import MessageFactory, UserFactory


class InboxPageTests(WebTest):
    url = reverse_lazy("accounts:inbox")

    def setUp(self) -> None:
        super().setUp()

        self.me = UserFactory.create()
        self.contact1 = UserFactory.create()
        self.contact2 = UserFactory.create()
        self.me.user_contacts.add(self.contact1)
        self.me.user_contacts.add(self.contact2)
        self.message1 = MessageFactory.create(sender=self.me, receiver=self.contact1)
        self.message2 = MessageFactory.create(receiver=self.me, sender=self.contact2)

        self.app.set_user(self.me)

    def test_show_last_conversation_without_other_user(self):
        response = self.app.get(self.url, auto_follow=True)

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message2.id)

    def test_show_conversation_with_user_specified(self):
        response = self.app.get(
            self.url, {"with": self.contact1.email}, auto_follow=True
        )

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message1.id)

    def test_send_message(self):
        response = self.app.get(
            self.url, {"with": self.contact1.email}, auto_follow=True
        )
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        form["content"] = "some msg"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "some msg")
        self.assertEqual(last_message.sender, self.me)
        self.assertEqual(last_message.receiver, self.contact1)

    @temp_private_root()
    def test_send_file(self):
        response = self.app.get(
            self.url, {"with": self.contact1.email}, auto_follow=True
        )
        self.assertEqual(response.status_code, 200)

        form = response.forms["message-form"]
        form["file"] = ("file.txt", b"test content")

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        last_message = Message.objects.order_by("-pk").first()
        self.assertEqual(last_message.content, "")
        self.assertEqual(last_message.sender, self.me)
        self.assertEqual(last_message.receiver, self.contact1)

        file = last_message.file
        self.assertEqual(file.name, "file.txt")
        self.assertEqual(file.read(), b"test content")

    def test_send_empty_message(self):
        response = self.app.get(
            self.url, {"with": self.contact1.email}, auto_follow=True
        )
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
        message_received = MessageFactory.create(receiver=self.me, sender=other_user)
        message_sent = MessageFactory.create(sender=self.me, receiver=other_user)

        for message in [message_sent, message_received]:
            self.assertFalse(message.seen)

        response = self.app.get(self.url, {"with": other_user.email}, auto_follow=True)
        self.assertEqual(response.status_code, 200)

        for message in [message_sent, message_received]:
            message.refresh_from_db()

        self.assertFalse(message_sent.seen)
        self.assertTrue(message_received.seen)


class BaseInboxPageSeleniumTests:
    options = None
    driver = None
    selenium = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.me = UserFactory.create(
            email="me@example.com", password="s3cret", is_staff=True
        )
        self.user1 = UserFactory.create(
            first_name="user", last_name="1", email="user1@example.com"
        )
        self.user2 = UserFactory.create(
            first_name="user", last_name="2", email="user2@example.com"
        )
        self.me.user_contacts.add(self.user1)
        self.me.user_contacts.add(self.user2)
        MessageFactory.create(sender=self.me, receiver=self.user1)
        MessageFactory.create(receiver=self.me, sender=self.user2)

    def tearDown(self):
        self.selenium.delete_all_cookies()

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
            receiver=self.me, sender=self.user2, content="Lorem ipsum dolor sit amet."
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
        self.selenium.get("%s%s" % (self.live_server_url, reverse_lazy("admin:login")))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("me@example.com")
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys("s3cret")
        self.selenium.find_element(By.XPATH, '//input[@type="submit"]').click()

    def when_i_navigate_to_page(self):
        self.selenium.get(
            "%s%s" % (self.live_server_url, reverse_lazy("accounts:inbox"))
        )


class InboxPageFirefoxSeleniumTests(
    FirefoxSeleniumTests, BaseInboxPageSeleniumTests, StaticLiveServerTestCase
):
    pass


class InboxPageChromeSeleniumTests(
    ChromeSeleniumTests, BaseInboxPageSeleniumTests, StaticLiveServerTestCase
):
    pass
