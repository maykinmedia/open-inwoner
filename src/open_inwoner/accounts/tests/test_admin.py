import os

from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest
from playwright.sync_api import Playwright, sync_playwright

from ..models import User
from .factories import UserFactory


class TestAdminUser(WebTest):
    def setUp(self):
        self.user = UserFactory(
            is_superuser=True, is_staff=True, email="john@example.com"
        )

    def test_user_is_created_without_case_sensitive_email(self):
        response = self.app.get(reverse("admin:accounts_user_add"), user=self.user)
        form = response.forms["user_form"]
        form["email"] = "john2@example.com"
        form["password1"] = "Abc123!@#"
        form["password2"] = "Abc123!@#"
        response = form.submit("_save")

        self.assertEqual(User.objects.count(), 2)

    def test_user_is_updated_without_case_sensitive_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "john2@example.com"
        response = form.submit("_save")

        existing_user = User.objects.get()

        self.assertEqual(existing_user.email, "john2@example.com")

    def test_user_is_updated_without_modifying_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["first_name"] = "Updated"
        response = form.submit("_save")

        existing_user = User.objects.get()

        self.assertEqual(existing_user.first_name, "Updated")
        self.assertEqual(existing_user.email, self.user.email)

    def test_user_not_created_with_case_sensitive_email(self):
        response = self.app.get(reverse("admin:accounts_user_add"), user=self.user)
        form = response.forms["user_form"]
        form["email"] = "John@example.com"
        form["password1"] = "Abc123!@#"
        form["password2"] = "Abc123!@#"
        response = form.submit("_save")

        self.assertContains(response, _("The user with this email already exists."))
        self.assertEqual(User.objects.count(), 1)

    def test_user_not_updated_with_case_sensitive_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "John@example.com"
        response = form.submit("_save")

        updated_user = User.objects.get()

        self.assertContains(response, _("The user with this email already exists."))
        self.assertEqual(self.user.email, updated_user.email)


from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class MyViewTests(StaticLiveServerTestCase):
    playwright: Playwright

    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

        cls.user = UserFactory(email="foo@example.com", password="secret")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def test_login(self):
        page = self.browser.new_page()
        page.goto("%s%s" % (self.live_server_url, "/accounts/login/"))
        page.screenshot(path="screenshot.png")
        page.wait_for_selector("text=Log in")
        page.fill("[name='username']", "foo@example.com")
        page.fill("[name='password']", "secret")
        page.click("text=Log in")
        self.assertEqual(page.url, "%s%s" % (self.live_server_url, "/profile/"))
        page.close()
