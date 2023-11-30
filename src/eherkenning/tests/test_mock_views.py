from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse, reverse_lazy

from furl import furl

RETURN_URL = "/"
CANCEL_URL = reverse("login")


class eHerkenningMockTestCase(TestCase):
    def assertNoEHerkenningURLS(self, response):
        # verify no links to eHerkenning remain in template
        self.assertNotContains(response, "://eherkenning.nl")
        self.assertNotContains(response, "://www.eherkenning.nl")


OVERRIDE_SETTINGS = dict(
    EHERKENNING_MOCK_APP_TITLE="FooBarBazz-MockApp",
    EHERKENNING_MOCK_RETURN_URL=RETURN_URL,  # url to redirect to after success
    EHERKENNING_MOCK_CANCEL_URL=CANCEL_URL,  # url to navigate to when users clicks 'cancel/annuleren'
)

MODIFY_SETTINGS = dict(
    AUTHENTICATION_BACKENDS={
        "append": [
            "eherkenning.mock.backends.eHerkenningBackend",
        ],
        "remove": [
            "eherkenning.backends.eHerkenningBackend",
        ],
    }
)


@patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
@override_settings(**OVERRIDE_SETTINGS)
@modify_settings(**MODIFY_SETTINGS)
class TestAppIndexTests(TestCase):
    def test_eherkenning_enabled(self, mock_solo):
        mock_solo.return_value.eherkenning_enabled = True

        url = reverse("login")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("eherkenning:login"))

    def test_eherkenning_disabled(self, mock_solo):
        mock_solo.return_value.eherkenning_enabled = False

        url = reverse("login")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("eherkenning:login"))


@override_settings(**OVERRIDE_SETTINGS)
@modify_settings(**MODIFY_SETTINGS)
class LoginViewTests(eHerkenningMockTestCase):
    def test_get_returns_http400_on_missing_params(self):
        url = reverse("eherkenning-mock:login")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

    def test_get_returns_valid_response(self):
        url = reverse("eherkenning-mock:login")
        data = {
            "acs": reverse("eherkenning:acs"),
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        response = self.client.get(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FooBarBazz-MockApp")
        self.assertContains(response, reverse("eherkenning-mock:password"))
        self.assertNoEHerkenningURLS(response)


@override_settings(**OVERRIDE_SETTINGS)
@modify_settings(**MODIFY_SETTINGS)
class PasswordLoginViewTests(eHerkenningMockTestCase):
    def test_get_returns_http400_on_missing_params(self):
        url = reverse("eherkenning-mock:password")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

    def test_get_returns_valid_response(self):
        url = reverse("eherkenning-mock:password")
        data = {
            "acs": reverse("eherkenning:acs"),
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        response = self.client.get(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FooBarBazz-MockApp")
        self.assertContains(response, reverse("eherkenning-mock:login"))
        self.assertNoEHerkenningURLS(response)

    def test_post_redirects_and_authenticates(self):
        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "29664887",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.client.post(url, data, follow=False)

        # it will redirect to our ACS
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("eherkenning:acs"), response["Location"])

        # follow the ACS redirect and get/create the user
        response = self.client.get(response["Location"], follow=False)

        User = get_user_model()
        user = User.eherkenning_objects.get(kvk="29664887")

        # follow redirect to 'next'
        self.assertRedirects(response, RETURN_URL)

        response = self.client.get(response["Location"], follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"].kvk, "29664887")

    def test_post_redirect_retains_acs_querystring_params(self):
        url = reverse("eherkenning-mock:password")
        params = {
            "acs": f"{reverse('eherkenning:acs')}?foo=bar",
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "29664887",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.client.post(url, data, follow=False)

        # it will redirect to our ACS
        expected_redirect = furl(reverse("eherkenning:acs")).set(
            {
                "foo": "bar",
                "kvk": "29664887",
                "next": RETURN_URL,
            }
        )
        self.assertRedirects(
            response, str(expected_redirect), fetch_redirect_response=False
        )


@override_settings(**OVERRIDE_SETTINGS)
@modify_settings(**MODIFY_SETTINGS)
class LogoutViewTests(TestCase):
    def test_logout(self):
        User = get_user_model()
        user = User.objects.create_user(email="testuser@localhost", password="test")
        self.client.force_login(user)

        url = reverse("eherkenning:logout")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse("_auth_user_id" in self.client.session)
