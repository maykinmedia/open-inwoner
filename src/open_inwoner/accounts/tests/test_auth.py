from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.configurations.models import SiteConfiguration

from ..models import User
from .factories import InviteFactory, UserFactory


class TestRegistrationFunctionality(WebTest):
    url = reverse_lazy("django_registration_register")

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

    def test_registration_inactive_user(self):
        inactive_user = UserFactory.create(is_active=False)

        register_page = self.app.get(self.url)
        form = register_page.forms["registration-form"]
        form["email"] = inactive_user.email
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["password1"] = "somepassword"
        form["password2"] = "somepassword"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("django_registration_complete"))

        inactive_user.refresh_from_db()

        self.assertTrue(inactive_user.is_active)
        self.assertEqual(inactive_user.first_name, "John")
        self.assertEqual(inactive_user.last_name, "Smith")
        self.assertEqual(inactive_user.contacts.count(), 0)

    def test_registration_with_invite(self):
        invite = InviteFactory.create(
            contact__created_by__email=self.user.email,
            contact__contact_user__is_active=False,
        )
        invitee = invite.invitee
        register_page = self.app.get(f"{self.url}?invite={invite.key}")
        form = register_page.forms["registration-form"]

        # check that email is prefilled and read-only
        self.assertEqual(form["email"].value, invitee.email)
        self.assertEqual(form["email"].attrs.get("readonly"), "readonly")

        form["password1"] = "somepassword"
        form["password2"] = "somepassword"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("django_registration_complete"))

        invitee.refresh_from_db()

        self.assertTrue(invitee.is_active)
        self.assertEqual(invitee.contacts.count(), 1)

        contact = invitee.contacts.get()
        self.assertEqual(contact.contact_user, invite.inviter)


class TestLoginLogoutFunctionality(WebTest):
    def setUp(self):
        # Create a user. We need to reset their password
        # because otherwise we do not have access to the raw one associated.
        self.user = UserFactory.create(password="test")

        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

    def test_login(self):
        """Test that a user is successfully logged in."""
        form = self.app.get(reverse("login")).forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "test"
        form.submit().follow()
        # Verify that the user has been authenticated
        self.assertIn("_auth_user_id", self.app.session)

    def test_login_for_inactive_user_shows_appropriate_message(self):
        # Change user to inactive
        self.user.is_active = False
        self.user.save()

        form = self.app.get(reverse("login")).forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "test"
        response = form.submit()

        self.assertEquals(response.context["errors"], [_("Deze account is inactief.")])

    def test_login_with_wrong_credentials_shows_appropriate_message(self):
        form = self.app.get(reverse("login")).forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "wrong_password"
        response = form.submit()

        self.assertEquals(
            response.context["errors"],
            [
                _(
                    "Voer een juiste e-mailadres en wachtwoord in. Let op dat beide velden hoofdlettergevoelig zijn."
                )
            ],
        )

    def test_logout(self):
        """Test that a user is able to log out and page redirects to root endpoint."""
        # Log out user and redirection
        logout_response = self.app.get(reverse("logout"), user=self.user)
        self.assertRedirects(logout_response, reverse("root"))
        self.assertFalse(logout_response.follow().context["user"].is_authenticated)
