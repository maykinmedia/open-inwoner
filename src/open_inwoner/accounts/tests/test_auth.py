from unittest.case import skip

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from ..models import User
from .factories import UserFactory


class TestRegistrationFunctionality(WebTest):
    def setUp(self):
        # Create a User instance that's not saved
        self.user = UserFactory.build()

    def test_registration_succeeds_with_right_user_input(self):
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        form["email"] = self.user.email
        form["first_name"] = self.user.first_name
        form["last_name"] = self.user.last_name
        form["password1"] = self.user.password
        form["password2"] = self.user.password
        form.submit()
        # Verify the registered user.
        registered_user = User.objects.get(email=self.user.email)
        self.assertEquals(registered_user.email, self.user.email)
        self.assertTrue(registered_user.check_password(self.user.password))

    def test_registration_fails_without_filling_out_first_name(self):
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        form["email"] = self.user.email
        form["last_name"] = self.user.last_name
        form["password1"] = self.user.password
        form["password2"] = self.user.password
        form.submit()
        # Verify that the user has not been registered
        user_query = User.objects.filter(email=self.user.email)
        self.assertEquals(user_query.count(), 0)

    def test_registration_fails_without_filling_out_last_name(self):
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        form["email"] = self.user.email
        form["first_name"] = self.user.first_name
        form["password1"] = self.user.password
        form["password2"] = self.user.password
        form.submit()
        # Verify that the user has not been registered
        user_query = User.objects.filter(email=self.user.email)
        self.assertEquals(user_query.count(), 0)


class TestLoginLogoutFunctionality(WebTest):
    def setUp(self):
        # Create a user. We need to reset their password
        # because otherwise we do not have access to the raw one associated.
        self.user = UserFactory.create(password="test")

    @skip
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
