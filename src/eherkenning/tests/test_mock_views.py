from hashlib import md5
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse

from furl import furl

from open_inwoner.kvk.branches import get_kvk_branch_number

RETURN_URL = "/"
CANCEL_URL = reverse("login")

User = get_user_model()


class eHerkenningMockTestCase(TestCase):
    def assertNoEHerkenningURLS(self, response):
        # verify no links to eHerkenning remain in template
        self.assertNotContains(response, "://eherkenning.nl")
        self.assertNotContains(response, "://www.eherkenning.nl")


OVERRIDE_SETTINGS = dict(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
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
        self.assertContains(response, "Dit is een mockup van de eHerkenning login flow")
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
        self.assertContains(response, "Dit is een mockup van de eHerkenning")
        self.assertContains(response, reverse("login"))
        self.assertNoEHerkenningURLS(response)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    def test_post_redirects_and_authenticates(self, mock_kvk):
        mock_kvk.return_value = [
            {"kvkNummer": "29664887", "vestigingsnummer": "1234"},
            {"kvkNummer": "29664887", "vestigingsnummer": "5678"},
        ]

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "29664887",
            "auth_pass": "company@localhost",
        }

        # post our password to the IDP
        response = self.client.post(url, data, follow=False)

        # it will redirect to our ACS
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("eherkenning:acs"), response["Location"])

        # follow the ACS redirect and get/create the user
        response = self.client.get(response["Location"], follow=False)

        # redirect to kvk/branches
        response = self.client.get(response["Location"])
        self.assertIn(reverse("kvk:branches"), response["Location"])

        # post branch_number, follow redirect back to register/necessary
        response = self.client.post(
            response["Location"], {"branch_number": "1234"}, follow=True
        )
        self.assertRedirects(response, reverse("profile:registration_necessary"))

        # check user kvk
        self.assertEqual(
            response.context["user"].kvk, User.eherkenning_objects.get().kvk
        )

        # check company branch number in session
        self.assertEqual(get_kvk_branch_number(self.client.session), "1234")

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    def test_redirect_flow_with_single_company(self, mock_kvk):
        """
        Assert that if the KvK API returns only a single company:
            1. the redirect flow passes automatically through `KvKLoginMiddleware`
            2. the company vestigingsnummer is stored in the session
        """
        mock_kvk.return_value = [
            {"kvkNummer": "29664887", "vestigingsnummer": "1234"},
        ]

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "29664887",
            "auth_pass": "company@localhost",
        }

        # post our password to the IDP
        response = self.client.post(url, data, follow=False)

        # it will redirect to our ACS
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("eherkenning:acs"), response["Location"])

        # follow the ACS redirect and get/create the user
        response = self.client.get(response["Location"], follow=True)

        user = User.objects.get(kvk="29664887")
        salt = "generate_email_from_bsn"
        hashed_kvk = md5(
            (salt + "29664887").encode(), usedforsecurity=False
        ).hexdigest()
        self.assertEqual(user.email, f"{hashed_kvk}@localhost")

        # check company branch number in session
        self.assertEqual(get_kvk_branch_number(self.client.session), "1234")

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    def test_redirect_flow_with_no_vestigingsnummer(self, mock_kvk):
        """
        Assert that if the KvK API returns only a single company without vestigingsnummer:
            1. the redirect flow passes automatically through `KvKLoginMiddleware`
            2. the company KvKNummer is stored in the session
        """
        mock_kvk.return_value = [
            {"kvkNummer": "29664887"},
        ]

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": RETURN_URL,
            "cancel": CANCEL_URL,
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "29664887",
            "auth_pass": "company@localhost",
        }

        # post our password to the IDP
        response = self.client.post(url, data, follow=False)

        # it will redirect to our ACS
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("eherkenning:acs"), response["Location"])

        # follow the ACS redirect and get/create the user
        response = self.client.get(response["Location"], follow=True)

        # check company branch number in session
        self.assertEqual(get_kvk_branch_number(self.client.session), "29664887")

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
