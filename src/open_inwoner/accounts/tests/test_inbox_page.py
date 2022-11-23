from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse_lazy

from django_webtest import WebTest
from privates.test import temp_private_root
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver

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
        response = self.app.get(self.url, auto_follow=True)

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message2.id)

    def test_show_conversation_with_user_specified(self):
        response = self.app.get(self.url, {"with": self.user1.email}, auto_follow=True)

        self.assertEqual(response.status_code, 200)
        conversations = response.context["conversations"]["object_list"]
        messages = response.context["conversation_messages"]

        self.assertEqual(conversations.count(), 2)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].id, self.message1.id)

    def test_send_message(self):
        response = self.app.get(self.url, {"with": self.user1.email}, auto_follow=True)
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
        response = self.app.get(self.url, {"with": self.user1.email}, auto_follow=True)
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
        response = self.app.get(self.url, {"with": self.user1.email}, auto_follow=True)
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
        ContactFactory.create(
            created_by=self.me, contact_user=self.user1, email=self.user1.email
        )
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


class MySeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.headless = True
        cls.selenium = WebDriver(options=options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_async_selector(self):
        # Create fixtures.
        me = UserFactory.create(
            email="johndoe@example.com", password="s3cret", is_staff=True
        )
        user1, user2 = UserFactory.create_batch(2)
        ContactFactory.create(created_by=me, contact_user=user1, email=user1.email)
        ContactFactory.create(created_by=me, contact_user=user2, email=user2.email)
        MessageFactory.create(sender=me, receiver=user1)
        MessageFactory.create(receiver=me, sender=user2)

        # Log in.
        self.selenium.get("%s%s" % (self.live_server_url, reverse_lazy("admin:login")))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("johndoe@example.com")
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys("s3cret")
        self.selenium.find_element(By.XPATH, '//input[@type="submit"]').click()

        # Go to messages page.
        self.selenium.get(
            "%s%s" % (self.live_server_url, reverse_lazy("accounts:inbox"))
        )

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
