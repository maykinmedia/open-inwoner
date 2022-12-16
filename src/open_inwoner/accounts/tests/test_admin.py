from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest

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
