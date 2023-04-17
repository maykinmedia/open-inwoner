from datetime import date
from urllib.parse import urlencode

from django.contrib.sites.models import Site
from django.core import mail
from django.test import override_settings
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest
from furl import furl

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.tests.mixins import HaalCentraalMixin

from ..choices import LoginTypeChoices
from ..models import User
from .factories import DigidUserFactory, InviteFactory, UserFactory


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
        self.assertEqual(registered_user.email, self.user.email)
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
        self.assertEqual(user_query.count(), 0)

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
        self.assertEqual(user_query.count(), 0)

    def test_registration_fails_with_invalid_first_name_characters(self):
        invalid_characters = "/\"\\,.:;'"

        for char in invalid_characters:
            with self.subTest(char=char):
                register_page = self.app.get(reverse("django_registration_register"))
                form = register_page.forms["registration-form"]
                form["email"] = self.user.email
                form["first_name"] = char
                form["last_name"] = self.user.last_name
                form["password1"] = self.user.password
                form["password2"] = self.user.password
                response = form.submit()
                expected_errors = {
                    "first_name": [
                        _("Uw invoer bevat een ongeldig teken: {char}").format(
                            char=char
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_registration_fails_with_invalid_last_name_characters(self):
        invalid_characters = "/\"\\,.:;'"

        for char in invalid_characters:
            with self.subTest(char=char):
                register_page = self.app.get(reverse("django_registration_register"))
                form = register_page.forms["registration-form"]
                form["email"] = self.user.email
                form["first_name"] = self.user.first_name
                form["last_name"] = char
                form["password1"] = self.user.password
                form["password2"] = self.user.password
                response = form.submit()
                expected_errors = {
                    "last_name": [
                        _("Uw invoer bevat een ongeldig teken: {char}").format(
                            char=char
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_registration_fails_with_case_sensitive_email(self):
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        user = UserFactory(email="user@example.com")
        form["email"] = "User@example.com"
        form["first_name"] = self.user.first_name
        form["last_name"] = self.user.last_name
        form["password1"] = self.user.password
        form["password2"] = self.user.password
        response = form.submit()
        expected_errors = {"email": [_("The user with this email already exists")]}
        user_query = User.objects.filter(email=self.user.email)
        self.assertEqual(user_query.count(), 0)
        self.assertEqual(response.context["form"].errors, expected_errors)

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
        self.assertEqual(list(User.objects.filter(email=contact.email)), [])

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

        new_user = User.objects.get(email=contact.email)
        invite.refresh_from_db()

        self.assertEqual(new_user.first_name, contact.first_name)
        self.assertEqual(new_user.last_name, contact.last_name)
        self.assertEqual(new_user.email, contact.email)
        self.assertEqual(invite.invitee, new_user)

        # reverse contact checks
        self.assertEqual(list(user.user_contacts.all()), [new_user])

    def test_invite_url_not_in_session_after_successful_registration(self):
        user = UserFactory()
        contact = UserFactory.build(email="test@testemail.com")
        invite = InviteFactory.create(
            inviter=user,
            invitee_email=contact.email,
            invitee_first_name=contact.first_name,
            invitee_last_name=contact.last_name,
        )
        invite = InviteFactory.create()
        url = invite.get_absolute_url()

        response = self.app.get(url)

        form = response.forms["invite-form"]
        response = form.submit()

        self.assertIn("invite_url", self.app.session.keys())

        register_page = self.app.get(f"{self.url}?invite={invite.key}")
        form = register_page.forms["registration-form"]

        form["password1"] = "somepassword"
        form["password2"] = "somepassword"

        response = form.submit()

        self.assertNotIn("invite_url", self.app.session.keys())

    def test_registration_active_user(self):
        """the user should be redirected to the registration complete page"""

        user = UserFactory.create()

        response = self.app.get(self.url, user=user)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("django_registration_complete"))

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


class TestDigid(HaalCentraalMixin, WebTest):
    csrf_checks = False
    url = reverse_lazy("django_registration_register")

    def test_registration_page_only_digid(self):
        response = self.app.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.html.find(id="registration-form"))

        digid_tag = response.html.find("a", title="Registreren met DigiD")
        self.assertIsNotNone(digid_tag)
        self.assertEqual(
            digid_tag.attrs["href"],
            furl(reverse("digid:login"))
            .add({"next": reverse("accounts:registration_necessary")})
            .url,
        )

    def test_registration_page_only_digid_with_invite(self):
        invite = InviteFactory.create()

        response = self.app.get(f"{self.url}?invite={invite.key}")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.html.find(id="registration-form"))

        digid_tag = response.html.find("a", title="Registreren met DigiD")
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

    def test_digid_fail_without_invite_redirects_to_login_page(self):
        self.assertNotIn("invite_url", self.client.session.keys())

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "w",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        self.assertRedirects(response, f"http://testserver{reverse('login')}")

    def test_digid_fail_without_invite_and_next_url_redirects_to_login_page(self):
        self.assertNotIn("invite_url", self.client.session.keys())

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": None,
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "w",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        self.assertRedirects(response, f"http://testserver{reverse('login')}")

    def test_digid_fail_with_invite_redirects_to_register_page(self):
        invite = InviteFactory()
        session = self.client.session
        session[
            "invite_url"
        ] = f"{reverse('django_registration_register')}?invite={invite.key}"
        session.save()

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": f"{reverse('accounts:registration_necessary')}?invite={invite.key}",
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "w",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.client.post(url, data, follow=True)

        self.assertRedirects(
            response,
            f"http://testserver{reverse('django_registration_register')}?invite={invite.key}",
        )

    def test_invite_url_not_in_session_after_successful_login(self):
        invite = InviteFactory()
        session = self.client.session
        session[
            "invite_url"
        ] = f"{reverse('django_registration_register')}?invite={invite.key}"
        session.save()

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": f"{reverse('accounts:registration_necessary')}?invite={invite.key}",
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "123456789",
            "auth_pass": "bar",
        }

        self.assertIn("invite_url", self.client.session.keys())

        # post our password to the IDP
        response = self.client.post(url, data, follow=True)

        self.assertRedirects(
            response,
            f"{reverse('accounts:registration_necessary')}?invite={invite.key}",
        )
        self.assertNotIn("invite_url", self.client.session.keys())

    @requests_mock.Mocker()
    def test_user_can_modify_only_email_when_digid_and_brp(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("accounts:registration_necessary"),
        }
        data = {
            "auth_name": "123456789",
            "auth_pass": "bar",
        }
        url = f"{url}?{urlencode(params)}"
        response = self.app.post(url, data).follow()

        form = response.follow().forms["necessary-form"]
        form["email"] = "updated@example.com"
        form["first_name"] = "JUpdated"
        form["last_name"] = "SUpdated"
        form.submit()

        user = User.objects.get(id=self.app.session["_auth_user_id"])

        self.assertTrue(user.is_prepopulated)
        self.assertEqual(user.email, "updated@example.com")
        self.assertEqual(user.first_name, "Merel")
        self.assertEqual(user.last_name, "Kooyman")

    @requests_mock.Mocker()
    def test_partial_response_from_haalcentraal_when_digid_and_brp(self, m):
        self._setUpService()

        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json={
                "personen": [
                    {
                        "naam": {
                            "voornamen": "Merel",
                        },
                    }
                ],
                "type": "RaadpleegMetBurgerservicenummer",
            },
        )
        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("accounts:registration_necessary"),
        }
        data = {
            "auth_name": "123456789",
            "auth_pass": "bar",
        }
        url = f"{url}?{urlencode(params)}"
        response = self.app.post(url, data).follow()
        user = User.objects.get(id=self.app.session["_auth_user_id"])

        # ensure user's first_name has been updated
        self.assertEqual(user.first_name, "Merel")
        self.assertEqual(user.last_name, "")
        self.assertTrue(user.email.endswith("@example.org"))

        # only email can be modified
        form = response.follow().forms["necessary-form"]
        form["email"] = "updated@example.org"
        form["first_name"] = "JUpdated"
        form.submit()

        user.refresh_from_db()

        self.assertEqual(user.first_name, "Merel")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "updated@example.org")

    @requests_mock.Mocker()
    def test_first_digid_login_updates_brp_fields(self, m):
        self._setUpService()
        self._setUpMocks_v_2(m)

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "123456782",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        user = User.objects.get(id=self.app.session["_auth_user_id"])

        self.assertEqual(user.first_name, "Merel")
        self.assertEqual(user.last_name, "Kooyman")
        self.assertEqual(user.birthday, date(1982, 4, 10))
        self.assertEqual(user.street, "King Olivereiland")
        self.assertEqual(user.housenumber, "64")
        self.assertEqual(user.city, "'s-Gravenhage")
        self.assertTrue(user.is_prepopulated)

    @requests_mock.Mocker()
    def test_existing_user_digid_login_updates_brp_fields(self, m):
        self._setUpService()

        user = DigidUserFactory()
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json={
                "personen": [
                    {
                        "naam": {
                            "voornamen": "UpdatedName",
                        },
                    }
                ],
                "type": "RaadpleegMetBurgerservicenummer",
            },
        )
        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": user.bsn,
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        user.refresh_from_db()

        self.assertEqual(user.first_name, "UpdatedName")

    @requests_mock.Mocker()
    def test_existing_user_digid_login_fails_brp_update_when_no_brp_service(self, m):
        user = DigidUserFactory()
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=200,
            json={
                "personen": [
                    {
                        "naam": {
                            "voornamen": "UpdatedName",
                        },
                    }
                ],
                "type": "RaadpleegMetBurgerservicenummer",
            },
        )
        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": user.bsn,
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        user.refresh_from_db()

        self.assertNotEqual(user.first_name, "UpdatedName")

    @requests_mock.Mocker()
    def test_existing_user_digid_login_fails_brp_update_when_brp_http_404(self, m):
        self._setUpService()

        user = DigidUserFactory()
        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_2.0.yaml"),
        )
        m.post(
            "https://personen/api/brp/personen",
            status_code=404,
        )
        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": user.bsn,
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        user.refresh_from_db()

        self.assertNotEqual(user.first_name, "UpdatedName")


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
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
            reverse("accounts:my_data"),
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

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

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

        response = self.app.get(f"{self.url}?invite={invite.key}", user=user)
        form = response.forms["necessary-form"]

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
        self.assertEqual(list(user.user_contacts.all()), [user_contact])

    def test_submit_not_unique_email(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

        form["email"] = "john@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"].as_text(),
            "* Een gebruiker met dit e-mailadres bestaat al",
        )

    def test_submit_with_case_sensitive_email_fails(self):
        UserFactory.create(email="john@example.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

        form["email"] = "John@example.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"

        response = form.submit()
        expected_errors = {"email": [_("The user with this email already exists")]}

        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_submit_not_unique_email_different_case(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

        form["email"] = "John@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["errors"].as_text(),
            "* Een gebruiker met dit e-mailadres bestaat al",
        )

    def test_submit_invalid_first_name_chars_fails(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        invalid_characters = "/\"\\,.:;'"

        for char in invalid_characters:
            with self.subTest(char=char):
                response = self.app.get(self.url, user=user)
                form = response.forms["necessary-form"]
                form["email"] = "user@example.com"
                form["first_name"] = char
                form["last_name"] = "Smith"
                response = form.submit()
                expected_errors = {
                    "first_name": [
                        _("Uw invoer bevat een ongeldig teken: {char}").format(
                            char=char
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_submit_invalid_last_name_chars_fails(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        invalid_characters = "/\"\\,.:;'"

        for char in invalid_characters:
            with self.subTest(char=char):
                response = self.app.get(self.url, user=user)
                form = response.forms["necessary-form"]
                form["email"] = "user@example.com"
                form["first_name"] = "John"
                form["last_name"] = char
                response = form.submit()
                expected_errors = {
                    "last_name": [
                        _("Uw invoer bevat een ongeldig teken: {char}").format(
                            char=char
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)


class TestLoginLogoutFunctionality(WebTest):
    def setUp(self):
        # Create a user. We need to reset their password
        # because otherwise we do not have access to the raw one associated.
        self.user = UserFactory.create(password="test")

        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

    def test_login_page_has_next_url(self):
        response = self.app.get(reverse("accounts:contact_list"))
        self.assertRedirects(
            response,
            furl(reverse("login")).add({"next": reverse("accounts:contact_list")}).url,
        )
        self.assertIn(
            furl("").add({"next": reverse("accounts:contact_list")}).url,
            response.follow(),
        )

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

        self.assertEqual(response.context["errors"], [_("Deze account is inactief.")])

    def test_login_with_wrong_credentials_shows_appropriate_message(self):
        form = self.app.get(reverse("login")).forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "wrong_password"
        response = form.submit()

        self.assertEqual(
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
        self.assertContains(response, _("Wachtwoord opnieuw instellen"))

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
