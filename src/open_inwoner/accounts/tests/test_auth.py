from django.contrib.sites.models import Site
from django.core import mail
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from django_webtest import WebTest
from furl import furl

from open_inwoner.configurations.models import SiteConfiguration

from ..choices import LoginTypeChoices
from ..models import User
from .factories import InviteFactory, UserFactory


class TestRegistrationFunctionality(WebTest):
    url = reverse_lazy("django_registration_register")

    def setUp(self):
        # Create a User instance that's not saved
        self.user = UserFactory.build()

        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"].as_text(), "* Deze gebruiker is gedeactiveerd"
        )

    def test_registration_with_invite(self):
        user = UserFactory()
        contact = UserFactory.build(email="test@testemail.com")
        invite = InviteFactory.create(
            inviter=user,
            invitee_email=contact.email,
            invitee_first_name=contact.first_name,
            invitee_last_name=contact.last_name,
        )
        self.assertFalse(User.objects.filter(email=contact.email).exists())

        register_page = self.app.get(f"{self.url}?invite={invite.key}")
        form = register_page.forms["registration-form"]

        # check that fields are prefilled with invite data
        self.assertEqual(form["email"].value, contact.email)
        self.assertEqual(form["first_name"].value, contact.first_name)
        self.assertEqual(form["last_name"].value, contact.last_name)

        form["password1"] = "somepassword"
        form["password2"] = "somepassword"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("django_registration_complete"))
        self.assertTrue(User.objects.filter(email=contact.email).exists())

        user = User.objects.get(email=contact.email)
        invite.refresh_from_db()

        self.assertEqual(user.first_name, contact.first_name)
        self.assertEqual(user.last_name, contact.last_name)
        self.assertEqual(user.email, contact.email)
        self.assertEqual(invite.invitee, user)

        # reverse contact checks
        self.assertEqual(user.user_contacts.count(), 1)

    def test_registration_active_user(self):
        """the user should be redirected to the registration complete page"""

        user = UserFactory.create()

        get_response = self.app.get(self.url, user=user)

        self.assertEqual(get_response.status_code, 302)
        self.assertEqual(get_response.url, reverse("django_registration_complete"))

    def test_registration_non_unique_email_different_case(self):
        UserFactory.create(email="john@smith.com")

        register_page = self.app.get(self.url)
        form = register_page.forms["registration-form"]
        form["email"] = "John@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["password1"] = "somepassword"
        form["password2"] = "somepassword"

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"].as_text(),
            "* Een gebruiker met dit e-mailadres bestaat al",
        )


class TestRegistrationDigid(WebTest):
    url = reverse_lazy("django_registration_register")

    def test_registration_page_only_digid(self):
        get_response = self.app.get(self.url)

        self.assertEqual(get_response.status_code, 200)
        self.assertIsNone(get_response.html.find(id="registration-form"))

        digid_tag = get_response.html.find("a", title="Registreren met DigiD")
        self.assertIsNotNone(digid_tag)
        self.assertEqual(
            digid_tag.attrs["href"],
            furl(reverse("digid:login"))
            .add({"next": reverse("accounts:registration_necessary")})
            .url,
        )

    def test_registration_page_only_digid_with_invite(self):
        invite = InviteFactory.create()

        get_response = self.app.get(f"{self.url}?invite={invite.key}")

        self.assertEqual(get_response.status_code, 200)
        self.assertIsNone(get_response.html.find(id="registration-form"))

        digid_tag = get_response.html.find("a", title="Registreren met DigiD")
        self.assertIsNotNone(digid_tag)
        necessary_url = (
            furl(reverse("accounts:registration_necessary"))
            .add({"invite": invite.key})
            .url
        )
        self.assertEqual(
            digid_tag.attrs["href"],
            furl(reverse("digid:login")).add({"next": necessary_url}).url,
        )


class TestRegistrationNecessary(WebTest):
    url = reverse_lazy("accounts:registration_necessary")

    def test_any_page_for_digid_user_redirect_to_necessary_fields(self):
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        urls = [
            reverse("root"),
            reverse("pdc:category_list"),
            reverse("accounts:my_profile"),
            reverse("accounts:inbox"),
            reverse("accounts:my_open_cases"),
            reverse("plans:plan_list"),
            reverse("general_faq"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.app.get(url, user=user)

                self.assertRedirects(
                    response, reverse("accounts:registration_necessary")
                )

    def test_submit_without_invite(self):
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        self.assertTrue(user.require_necessary_fields())

        get_response = self.app.get(self.url, user=user)
        form = get_response.forms["necessary-form"]

        form["email"] = "john@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("django_registration_complete"))

        user.refresh_from_db()

        self.assertFalse(user.require_necessary_fields())
        self.assertEqual(user.email, "john@smith.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Smith")

    def test_submit_with_invite(self):
        user = UserFactory()
        contact = UserFactory.build()
        invite = InviteFactory.create(
            inviter=user,
            invitee_email=contact.email,
            invitee_first_name=contact.first_name,
            invitee_last_name=contact.last_name,
        )

        get_response = self.app.get(f"{self.url}?invite={invite.key}", user=user)
        form = get_response.forms["necessary-form"]

        # assert initials are retrieved from invite
        self.assertEqual(form["email"].value, contact.email)
        self.assertEqual(form["first_name"].value, contact.first_name)
        self.assertEqual(form["last_name"].value, contact.last_name)

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("django_registration_complete"))

        user_contact = User.objects.get(email=contact.email)
        invite.refresh_from_db()

        self.assertEqual(user_contact.first_name, contact.first_name)
        self.assertEqual(user_contact.last_name, contact.last_name)
        self.assertEqual(user_contact.email, contact.email)
        self.assertEqual(user.user_contacts.count(), 1)

    def test_submit_not_unique_email(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )

        get_response = self.app.get(self.url, user=user)
        form = get_response.forms["necessary-form"]

        form["email"] = "john@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"].as_text(),
            "* Een gebruiker met dit e-mailadres bestaat al",
        )

    def test_submit_not_unique_email_different_case(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )

        get_response = self.app.get(self.url, user=user)
        form = get_response.forms["necessary-form"]

        form["email"] = "John@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"].as_text(),
            "* Een gebruiker met dit e-mailadres bestaat al",
        )


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
                    "Voer een juiste E-mailadres en wachtwoord in. Let op dat beide velden hoofdlettergevoelig zijn."
                )
            ],
        )

    def test_logout(self):
        """Test that a user is able to log out and page redirects to root endpoint."""
        # Log out user and redirection
        logout_response = self.app.get(reverse("logout"), user=self.user)
        self.assertRedirects(logout_response, reverse("root"))
        self.assertFalse(logout_response.follow().context["user"].is_authenticated)


class TestPasswordResetFunctionality(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()

    def test_password_reset_form_custom_template_is_rendered(self):
        response = self.app.get(reverse("password_reset"))
        self.assertContains(response, _("Mijn wachtwoord opnieuw instellen"))

    def test_password_reset_email_contains_proper_data(self):
        current_site = Site.objects.get_current()
        self.app.post(reverse("password_reset"), {"email": self.user.email})
        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        body = sent_mail.body
        self.assertEqual(
            _("Wachtwoordherinitialisatie voor {domain}").format(
                domain=current_site.domain
            ),
            sent_mail.subject,
        )
        self.assertIn(
            _(
                "U ontvangt deze e-mail, omdat u een aanvraag voor opnieuw instellen van het wachtwoord voor uw account op {domain} hebt gedaan."
            ).format(domain=current_site.domain),
            body,
        )
        self.assertIn(
            _("Uw gebruikersnaam, mocht u deze vergeten zijn: {user_email}").format(
                user_email=self.user.email
            ),
            body,
        )

    def test_password_reset_confirm_custom_template_is_rendered(self):
        response = self.app.post(reverse("password_reset"), {"email": self.user.email})
        token = response.context[0]["token"]
        uid = response.context[0]["uid"]
        confirm_response = self.app.get(
            reverse("password_reset_confirm", kwargs={"token": token, "uidb64": uid})
        ).follow()
        self.assertContains(confirm_response, _("Mijn wachtwoord wijzigen"))

    def test_custom_password_reset_form_sends_email_when_user_is_default(self):
        self.app.post(reverse("password_reset"), {"email": self.user.email})
        self.assertEqual(len(mail.outbox), 1)

    def test_custom_password_reset_form_does_not_send_email_when_user_is_digid(self):
        digid_user = UserFactory(
            login_type=LoginTypeChoices.digid, email="john@smith.nl"
        )
        self.app.post(reverse("password_reset"), {"email": digid_user.email})
        self.assertEqual(len(mail.outbox), 0)


class TestPasswordChange(WebTest):
    def setUp(self):
        self.user = UserFactory()

    def test_password_change_form_custom_template_is_rendered(self):
        response = self.app.get(reverse("password_change"), user=self.user)
        self.assertContains(response, _("Wachtwoordwijziging"))

    def test_password_change_form_done_custom_template_is_rendered(self):
        response = self.app.get(reverse("password_change_done"), user=self.user)
        self.assertContains(response, _("Uw wachtwoord is gewijzigd."))

    def test_password_change_button_is_rendered_with_default_login_type(self):
        response = self.app.get(reverse("accounts:my_profile"), user=self.user)
        self.assertContains(response, _("Wijzig wachtwoord"))

    def test_password_change_button_is_not_rendered_with_digid_login_type(self):
        digid_user = UserFactory(
            login_type=LoginTypeChoices.digid, email="john@smith.nl"
        )
        response = self.app.get(reverse("accounts:my_profile"), user=digid_user)
        self.assertNotContains(response, _("Wijzig wachtwoord"))

    def test_anonymous_user_is_redirected_to_login_page_if_password_change_is_accessed(
        self,
    ):
        response = self.app.get(reverse("password_change"))
        expected_url = (
            furl(reverse("login")).add({"next": reverse("password_change")}).url
        )
        self.assertRedirects(response, expected_url)
