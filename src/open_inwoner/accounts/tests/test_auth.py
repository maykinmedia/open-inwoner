from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from ..models import User
from .factories import UserFactory

# Constants.
TEST_USER = {
    "email": "test_user@maykin.nl",
    "first_name": "Bruce",
    "last_name": "Lee",
    "password": "28990As#",
}


class TestRegistrationFunctionality(WebTest):
    def test_registration_succeeds_with_right_user_input(self):
        register_page = self.app.get(reverse("django_registration_register"))

        form = register_page.forms["registration-form"]
        form["email"] = TEST_USER["email"]
        form["first_name"] = TEST_USER["first_name"]
        form["last_name"] = TEST_USER["last_name"]
        form["password1"] = TEST_USER["password"]
        form["password2"] = TEST_USER["password"]
        form.submit()

        # Verify the registered user.
        registered_user = User.objects.get(email=TEST_USER["email"])
        self.assertEquals(registered_user.email, TEST_USER["email"])
        self.assertTrue(registered_user.check_password(TEST_USER["password"]))

    def test_registration_fails_without_filling_out_first_name(self):
        register_page = self.app.get(reverse("django_registration_register"))

        form = register_page.forms["registration-form"]
        form["email"] = TEST_USER["email"]
        form["last_name"] = TEST_USER["last_name"]
        form["password1"] = TEST_USER["password"]
        form["password2"] = TEST_USER["password"]
        form.submit()

        # Verify that the user has not been registered
        user_query = User.objects.filter(email=TEST_USER["email"])
        self.assertEquals(user_query.count(), 0)

    def test_registration_fails_without_filling_out_last_name(self):
        register_page = self.app.get(reverse("django_registration_register"))

        form = register_page.forms["registration-form"]
        form["email"] = TEST_USER["email"]
        form["first_name"] = TEST_USER["first_name"]
        form["password1"] = TEST_USER["password"]
        form["password2"] = TEST_USER["password"]
        form.submit()

        # Verify that the user has not been registered
        user_query = User.objects.filter(email=TEST_USER["email"])
        self.assertEquals(user_query.count(), 0)


class TestLoginLogoutFunctionality(WebTest):
    def setUp(self):
        # Create a user. We need to reset their password
        # because otherwise we do not have access to the raw one associated.
        self.user = UserFactory.create(password="test")

    def test_login(self):
        """Test that a user is successfully logged in."""

        form = self.app.get(reverse("login")).forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "test"

        response = form.submit().follow()
        self.assertTrue(response.context["user"].is_authenticated)

    def test_logout(self):
        """Test that a user is able to log out and page redirects to root endpoint."""

        # Log out user and redirection
        logout_response = self.app.get(reverse("logout"), user=self.user)
        self.assertRedirects(logout_response, reverse("root"))
        self.assertFalse(logout_response.follow().context["user"].is_authenticated)
