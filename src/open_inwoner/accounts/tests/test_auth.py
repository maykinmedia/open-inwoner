from unittest.mock import ANY, patch
from urllib.parse import urlencode

from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site
from django.core import mail
from django.core.signing import TimestampSigner
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest
from freezegun import freeze_time
from furl import furl
from pyquery import PyQuery as PQ

from open_inwoner.accounts.choices import NotificationChannelChoice
from open_inwoner.accounts.signals import KvKClient, update_user_on_login
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.tests.mixins import HaalCentraalMixin
from open_inwoner.kvk.branches import get_kvk_branch_number
from open_inwoner.kvk.tests.factories import CertificateFactory
from open_inwoner.openklant.tests.data import MockAPIReadPatchData
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin

from ...cms.collaborate.cms_apps import CollaborateApphook
from ...cms.profile.cms_apps import ProfileApphook
from ...cms.tests import cms_tools
from ...utils.test import ClearCachesMixin
from ...utils.tests.helpers import AssertRedirectsMixin
from ..choices import LoginTypeChoices
from ..models import OpenIDDigiDConfig, OpenIDEHerkenningConfig, User
from .factories import (
    DigidUserFactory,
    InviteFactory,
    NewDigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
)

RETURN_URL = "/"
CANCEL_URL = reverse("login")


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class DigiDRegistrationTest(
    AssertRedirectsMixin, AssertTimelineLogMixin, HaalCentraalMixin, WebTest
):
    """Tests concerning the registration of DigiD users"""

    csrf_checks = False
    url = reverse_lazy("django_registration_register")

    @classmethod
    def setUpTestData(cls):
        cls.homepage = cms_tools.create_homepage()

    @patch("open_inwoner.accounts.models.OpenIDDigiDConfig.get_solo")
    def test_registration_page_only_digid(self, mock_solo):
        for oidc_enabled in [True, False]:
            with self.subTest(oidc_enabled=oidc_enabled):
                mock_solo.return_value.enabled = oidc_enabled

                digid_url = (
                    reverse("digid_oidc:init")
                    if oidc_enabled
                    else reverse("digid:login")
                )

                response = self.app.get(self.url)

                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.html.find(id="registration-form"))

                digid_tag = response.html.find("a", title="Registreren met DigiD")
                self.assertIsNotNone(digid_tag)
                self.assertEqual(
                    digid_tag.attrs["href"],
                    furl(digid_url)
                    .add({"next": reverse("profile:registration_necessary")})
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
            furl(reverse("profile:registration_necessary"))
            .add({"invite": invite.key})
            .url
        )
        self.assertEqual(
            digid_tag.attrs["href"],
            furl(reverse("digid:login")).add({"next": necessary_url}).url,
        )

    @patch("digid_eherkenning.validators.Proef11ValidatorBase.__call__")
    def test_digid_fail_without_invite_redirects_to_login_page(self, m):
        # disable mock form validation to check redirect
        m.return_value = True

        self.assertNotIn("invite_url", self.client.session.keys())

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("pages-root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "w",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        self.assertRedirectsLogin(response, with_host=True)

    @patch("digid_eherkenning.validators.Proef11ValidatorBase.__call__")
    def test_digid_fail_without_invite_and_next_url_redirects_to_login_page(self, m):
        # disable mock form validation to check redirect
        m.return_value = True

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

        self.assertRedirectsLogin(response, with_host=True)

    @patch("digid_eherkenning.validators.Proef11ValidatorBase.__call__")
    def test_digid_fail_with_invite_redirects_to_register_page(self, m):
        # disable mock form validation to check redirect
        m.return_value = True
        invite = InviteFactory()
        session = self.client.session
        session[
            "invite_url"
        ] = f"{reverse('django_registration_register')}?invite={invite.key}"
        session.save()

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": f"{reverse('profile:registration_necessary')}?invite={invite.key}",
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
            "next": f"{reverse('profile:registration_necessary')}?invite={invite.key}",
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "533458225",
            "auth_pass": "bar",
        }

        self.assertIn("invite_url", self.client.session.keys())

        # post our password to the IDP
        response = self.client.post(url, data, follow=True)

        self.assertRedirects(
            response,
            f"{reverse('profile:registration_necessary')}?invite={invite.key}",
        )
        self.assertNotIn("invite_url", self.client.session.keys())

    @requests_mock.Mocker()
    def test_user_can_modify_only_email_when_digid_and_brp(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("profile:registration_necessary"),
        }
        data = {
            "auth_name": "533458225",
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
    def test_notification_settings_with_cms_page_published(self, m):
        """
        Assert that notification settings can be changed via the necessary-fields form
        if the corresponding CMS pages are published. Fields corresponding to unpublished
        pages should not be present.
        """
        MockAPIReadPatchData.setUpServices()
        mock_api_data = MockAPIReadPatchData().install_mocks(m)

        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = True
        config.save()

        # reset noise from signals
        m.reset_mock()
        self.clearTimelineLogs()

        cms_tools.create_apphook_page(
            CollaborateApphook,
            parent_page=self.homepage,
        )

        invite = InviteFactory()

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": f"{reverse('profile:registration_necessary')}?invite={invite.key}",
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": mock_api_data.user.bsn,
            "auth_pass": "bar",
        }

        # post our password to the IDP
        response = self.app.post(url, data).follow().follow()

        necessary_form = response.forms["necessary-form"]

        self.assertNotIn("cases_notifications", necessary_form.fields)
        self.assertNotIn("messages_notifications", necessary_form.fields)

        necessary_form["plans_notifications"] = False
        necessary_form[
            "case_notification_channel"
        ] = NotificationChannelChoice.digital_only
        necessary_form.submit()

        user = User.objects.get(bsn=data["auth_name"])

        self.assertEqual(user.cases_notifications, True)
        self.assertEqual(user.messages_notifications, True)
        self.assertEqual(user.plans_notifications, False)
        self.assertEqual(
            user.case_notification_channel, NotificationChannelChoice.digital_only
        )

        # check klant api update
        self.assertTrue(mock_api_data.matchers[0].called)
        klant_patch_data = mock_api_data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "toestemmingZaakNotificatiesAlleenDigitaal": True,
            },
        )
        # only check logs for klant api update
        dump = self.getTimelineLogDump()
        msg = "patched klant from user profile edit with fields: toestemmingZaakNotificatiesAlleenDigitaal"
        assert msg in dump

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
            "next": reverse("profile:registration_necessary"),
        }
        data = {
            "auth_name": "533458225",
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
            "next": reverse("pages-root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "533458225",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        user = User.objects.get(id=self.app.session["_auth_user_id"])

        self.assertEqual(user.first_name, "Merel")
        self.assertEqual(user.last_name, "Kooyman")
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
            "next": reverse("pages-root"),
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
            "next": reverse("pages-root"),
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
            "next": reverse("pages-root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": user.bsn,
            "auth_pass": "bar",
        }
        # post our password to the IDP
        self.app.post(url, data).follow()

        user.refresh_from_db()

        self.assertNotEqual(user.first_name, "UpdatedName")


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class eHerkenningRegistrationTest(AssertRedirectsMixin, WebTest):
    """Tests concerning the registration of eHerkenning users"""

    csrf_checks = False
    url = reverse_lazy("django_registration_register")

    @classmethod
    def setUpTestData(cls):
        cms_tools.create_homepage()

    @patch("open_inwoner.accounts.models.OpenIDEHerkenningConfig.get_solo")
    @patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
    def test_registration_page_eherkenning(self, mock_solo, mock_eherkenning_config):
        mock_solo.return_value.eherkenning_enabled = True
        mock_solo.return_value.login_allow_registration = False

        for oidc_enabled in [True, False]:
            with self.subTest(oidc_enabled=oidc_enabled):
                mock_eherkenning_config.return_value.enabled = oidc_enabled

                eherkenning_url = (
                    reverse("eherkenning_oidc:init")
                    if oidc_enabled
                    else reverse("eherkenning:login")
                )

                response = self.app.get(self.url)

                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.html.find(id="registration-form"))

                eherkenning_tag = response.html.find(
                    "a", title="Registreren met eHerkenning"
                )
                self.assertIsNotNone(eherkenning_tag)
                self.assertEqual(
                    eherkenning_tag.attrs["href"],
                    furl(eherkenning_url)
                    .add({"next": reverse("profile:registration_necessary")})
                    .url,
                )

    @patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
    def test_registration_page_eherkenning_with_invite(self, mock_solo):
        mock_solo.return_value.eherkenning_enabled = True
        mock_solo.return_value.login_allow_registration = False

        invite = InviteFactory.create()

        response = self.app.get(f"{self.url}?invite={invite.key}")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.html.find(id="registration-form"))

        eherkenning_tag = response.html.find("a", title="Registreren met eHerkenning")
        self.assertIsNotNone(eherkenning_tag)
        necessary_url = (
            furl(reverse("profile:registration_necessary"))
            .add({"invite": invite.key})
            .url
        )
        self.assertEqual(
            eherkenning_tag.attrs["href"],
            furl(reverse("eherkenning:login")).add({"next": necessary_url}).url,
        )

    @patch("eherkenning.validators.KVKValidator.__call__")
    def test_eherkenning_fail_without_invite_redirects_to_login_page(self, m):
        # disable mock form validation to check redirect
        m.return_value = True

        self.assertNotIn("invite_url", self.client.session.keys())

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning-acs"),
            "next": reverse("pages-root"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "w",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow()

        self.assertRedirectsLogin(response, with_host=True)

    @patch(
        "open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk",
        return_value="",
        autospec=True,
    )
    @patch(
        "open_inwoner.accounts.views.auth.OpenZaakConfig.get_solo",
        return_value=OpenZaakConfig(fetch_eherkenning_zaken_with_rsin=True),
        autospec=True,
    )
    def test_login_as_eenmanszaak_blocked(
        self, mock_oz_config, mock_retrieve_rsin_with_kvk
    ):
        url = reverse("eherkenning-mock:password")
        params = {
            "acs": f"http://testserver{reverse('eherkenning:acs')}",
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
        response = self.client.get(response["Location"])

        # User is logged out and redirected to login view
        self.assertNotIn("_auth_user_id", self.app.session)
        self.assertRedirectsLogin(response, with_host=True)

    @patch("eherkenning.validators.KVKValidator.__call__")
    def test_eherkenning_fail_without_invite_and_next_url_redirects_to_login_page(
        self, m
    ):
        # disable mock form validation to check redirect
        m.return_value = True

        self.assertNotIn("invite_url", self.client.session.keys())

        url = reverse("eherkenning-mock:password")
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

        self.assertRedirectsLogin(response, with_host=True)

    @patch("eherkenning.validators.KVKValidator.__call__")
    def test_eherkenning_fail_with_invite_redirects_to_register_page(self, m):
        # disable mock form validation to check redirect
        m.return_value = True
        invite = InviteFactory()
        session = self.client.session
        session[
            "invite_url"
        ] = f"{reverse('django_registration_register')}?invite={invite.key}"
        session.save()

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": f"{reverse('profile:registration_necessary')}?invite={invite.key}",
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

    @patch(
        "open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk",
        return_value="123456789",
        autospec=True,
    )
    @patch(
        "open_inwoner.kvk.client.KvKClient.get_all_company_branches",
        autospec=True,
    )
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
        autospec=True,
    )
    def test_invite_url_not_in_session_after_successful_login(
        self,
        mock_solo,
        mock_kvk,
        mock_retrieve_rsin_with_kvk,
    ):
        mock_kvk.return_value = [
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        invite = InviteFactory()
        session = self.client.session
        session[
            "invite_url"
        ] = f"{reverse('django_registration_register')}?invite={invite.key}"
        session.save()

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": f"{reverse('profile:registration_necessary')}?invite={invite.key}",
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "12345678",
            "auth_pass": "bar",
        }

        self.assertIn("invite_url", self.client.session.keys())

        # post our password to the IDP
        response = self.client.post(url, data, follow=False)

        # follow redirect flow
        res = self.client.get(response["Location"])

        self.assertRedirects(
            res,
            f"{reverse('profile:registration_necessary')}?invite={invite.key}",
            fetch_redirect_response=False,
        )
        self.assertNotIn("invite_url", self.client.session.keys())

        # check company branch number in session
        self.assertEqual(get_kvk_branch_number(self.client.session), None)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_redirect_flow_with_no_vestigingsnummer(self, mock_solo, mock_kvk):
        """
        Assert that if the KvK API returns only a single company without vestigingsnummer:
            1. the redirect flow passes automatically through `KvKLoginMiddleware`
            2. the company KvKNummer is stored in the session
        """
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        user = eHerkenningUserFactory.create(
            kvk="12345678", rsin="123456789", email="user-12345678@localhost"
        )

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": "/",
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "12345678",
            "auth_pass": "foo",
        }

        response = self.client.get(url, user=user)

        # post our password to the IDP
        response = self.client.post(url, data, user=user, follow=True)
        self.assertRedirects(
            response,
            reverse("profile:registration_necessary"),
        )

        # check company branch number in session
        self.assertEqual(get_kvk_branch_number(self.client.session), None)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_eherkenning_user_is_redirected_to_necessary_registration(
        self, mock_solo, mock_kvk
    ):
        """
        eHerkenning users that do not have their email filled in should be redirected to
        the registration form
        """
        mock_kvk.return_value = [
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        user = eHerkenningUserFactory.create(kvk="12345678", email="example@localhost")

        response = self.app.get(reverse("pages-root"), user=user)

        # redirect to /kvk/branches/
        self.assertRedirects(
            response, reverse("kvk:branches"), fetch_redirect_response=False
        )

        res = self.app.post(response["Location"], {"branch_number": "1234"})

        # redirect to /register/necessary/
        self.assertRedirects(res, reverse("profile:registration_necessary"))


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class EmailPasswordRegistrationTest(WebTest):
    """
    Tests concerning the registration of non-digid users (email + password)
    """

    url = reverse_lazy("django_registration_register")

    def setUp(self):
        # Create a User instance that's not saved
        self.user = UserFactory.build(first_name="John", last_name="Doe")

        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

    def test_registration_succeeds_with_right_user_input(self):
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        form["email"] = self.user.email
        form["first_name"] = self.user.first_name
        form["infix"] = ""
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
        invalid_characters = '<>#/"\\,.:;'
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["email"] = self.user.email
                form["first_name"] = char
                form["last_name"] = self.user.last_name
                form["password1"] = self.user.password
                form["password2"] = self.user.password
                response = form.submit()
                expected_errors = {
                    "first_name": [
                        _(
                            "Please make sure your input contains only valid characters "
                            "(letters, numbers, apostrophe, dash, space)."
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_registration_fails_with_invalid_last_name_characters(self):
        invalid_characters = '<>#/"\\,.:;'
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["email"] = self.user.email
                form["first_name"] = self.user.first_name
                form["last_name"] = char
                form["password1"] = self.user.password
                form["password2"] = self.user.password
                response = form.submit()
                expected_errors = {
                    "last_name": [
                        _(
                            "Please make sure your input contains only valid characters "
                            "(letters, numbers, apostrophe, dash, space)."
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_registration_fails_with_non_diverse_password(self):
        passwords = [
            "NODIGITS",
            "nodigits",
            "NoDigits",
            "1238327879",
            "pass_word-123",
            "PASS_WORD-123",
            "UPPERCASE123",
            "lowercase123",
        ]
        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]

        for password in passwords:
            with self.subTest(password=password):
                form["email"] = self.user.email
                form["first_name"] = self.user.first_name
                form["last_name"] = self.user.last_name
                form["password1"] = password
                form["password2"] = password
                response = form.submit()
                expected_errors = {
                    "password2": [
                        _(
                            "Your password must contain at least 1 upper-case letter, "
                            "1 lower-case letter, 1 digit."
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

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

        form["password1"] = "SomePassword123"
        form["password2"] = "SomePassword123"

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pages-root"))
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

        form["password1"] = "SomePassword123"
        form["password2"] = "SomePassword123"

        response = form.submit()

        self.assertNotIn("invite_url", self.app.session.keys())

    def test_registration_active_user(self):
        """the user should be redirected to the homepage"""

        user = UserFactory.create()

        response = self.app.get(self.url, user=user)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pages-root"))

    def test_registration_succeeds_with_2fa_sms_and_phonenumber(self):
        self.config.login_2fa_sms = True
        self.config.save()

        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        form["email"] = self.user.email
        form["first_name"] = self.user.first_name
        form["last_name"] = self.user.last_name
        form["phonenumber"] = self.user.phonenumber
        form["password1"] = self.user.password
        form["password2"] = self.user.password
        form.submit()
        # Verify the registered user.
        registered_user = User.objects.get(email=self.user.email)
        self.assertEqual(registered_user.email, self.user.email)
        self.assertTrue(registered_user.check_password(self.user.password))

    def test_registration_fails_with_2fa_sms_and_no_phonenumber(self):
        self.config.login_2fa_sms = True
        self.config.save()

        register_page = self.app.get(reverse("django_registration_register"))
        form = register_page.forms["registration-form"]
        form["email"] = self.user.email
        form["first_name"] = self.user.first_name
        form["last_name"] = self.user.last_name
        form["password1"] = self.user.password
        form["password2"] = self.user.password
        response = form.submit()

        self.assertEqual(
            response.context["form"].errors,
            {"phonenumber": [_("Dit veld is vereist.")]},
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class DuplicateEmailRegistrationTest(WebTest):
    """
    DigiD/eHerkenning users should be able to register with email addresses that are already in use.
    Other users should not be able to register with duplicate emails.
    """

    # TODO ideally we want to test with CSRF checks, so we can spot CSRF issues
    csrf_checks = False
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.msg_dupes = _("This email is already taken.")
        cls.msg_inactive = _("This account has been deactivated")

    def test_digid_user_success(self):
        """Assert that digid users can register with duplicate emails"""
        test_user = DigidUserFactory.create(
            email="test@example.com",
            bsn="648197724",
        )

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("profile:registration_necessary"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            # different BSN
            "auth_name": "533458225",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow().follow()

        form = response.forms["necessary-form"]
        # same email
        form["email"] = "test@example.com"
        form["first_name"] = "JUpdated"
        form["last_name"] = "SUpdated"
        form.submit().follow()

        users = User.objects.filter(email__iexact=test_user.email)

        self.assertEqual(users.count(), 2)
        self.assertEqual(users.first().email, "test@example.com")
        self.assertEqual(users.last().email, "test@example.com")

    @patch(
        "open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk",
        return_value="123456789",
        autospec=True,
    )
    @patch(
        "open_inwoner.kvk.client.KvKClient.get_all_company_branches",
        autospec=True,
    )
    def test_eherkenning_user_success(self, mock_kvk, mock_retrieve_rsin_with_kvk):
        """Assert that eHerkenning users can register with duplicate emails"""

        mock_kvk.return_value = [
            {
                "kvkNummer": "12345678",
                "vestigingsnummer": "1234",
                "naam": "Mijn bedrijf",
            },
            {
                "kvkNummer": "12345678",
                "vestigingsnummer": "5678",
                "naam": "Mijn bedrijf",
            },
        ]

        test_user = eHerkenningUserFactory.create(
            email="test@localhost",
            kvk="64819772",
            rsin="123456789",
        )

        url = reverse("eherkenning-mock:password")
        params = {
            "acs": reverse("eherkenning:acs"),
            "next": reverse("kvk:branches"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            # different KvK
            "auth_name": "12345678",
            "auth_pass": "bar",
        }
        response = self.app.post(url, data).follow()

        # select company branch
        response = self.app.get(response["Location"])
        form = response.forms["eherkenning-branch-form"]
        form["branch_number"] = "5678"
        response = form.submit().follow()

        # fill in necessary fields form
        form = response.forms["necessary-form"]

        self.assertEqual(form["email"].value, "")
        self.assertNotIn("first_name", form.fields)
        self.assertNotIn("last_name", form.fields)

        # same email
        form["email"] = "test@localhost"
        form.submit().follow()

        users = User.objects.filter(email__iexact=test_user.email)

        self.assertEqual(users.count(), 2)
        self.assertEqual(users.first().email, "test@localhost")
        self.assertEqual(users.last().email, "test@localhost")

    # def test_digid_user_cannot_reregister_inactive_duplicate_email(self):
    #     inactive_user = DigidUserFactory.create(
    #         email="test@example.com",
    #         bsn="123456789",
    #         is_active=False,
    #         first_name="",
    #         last_name="",
    #         is_prepopulated=True,
    #     )

    #     url = reverse("digid-mock:password")
    #     params = {
    #         "acs": reverse("acs"),
    #         "next": reverse("profile:registration_necessary"),
    #     }
    #     url = f"{url}?{urlencode(params)}"

    #     data = {
    #         # same BSN
    #         "auth_name": "123456789",
    #         "auth_pass": "bar",
    #     }
    #     # post our password to the IDP
    #     response = self.app.post(url, data).follow().follow()

    #     form = response.forms["necessary-form"]
    #     form["email"] = "test@example.com"
    #     form["first_name"] = "JUpdated"
    #     form["last_name"] = "SUpdated"
    #     response = form.submit()

    #     expected_errors = {"email": [self.msg_inactive]}

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.context["form"].errors, expected_errors)

    #     users = User.objects.filter(email__iexact=inactive_user.email)

    #     self.assertEqual(users.count(), 1)

    def test_digid_user_non_digid_duplicate_fail(self):
        """
        Assert that digid user cannot register with email that belongs to a non-digid
        user
        """
        existing_user = UserFactory.create(
            email="test@example.com",
            login_type=LoginTypeChoices.default,
        )

        url = reverse("digid-mock:password")
        params = {
            "acs": reverse("acs"),
            "next": reverse("profile:registration_necessary"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "533458225",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow().follow()

        form = response.forms["necessary-form"]
        form["email"] = "test@example.com"
        form["first_name"] = "JUpdated"
        form["last_name"] = "SUpdated"
        response = form.submit()

        expected_errors = {"email": [self.msg_dupes]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

        users = User.objects.filter(email__iexact=existing_user.email)

        self.assertEqual(users.count(), 1)

    def test_digid_user_can_edit_profile(self):
        """
        Assert that digid user can edit their profile (the email of the same user
        is not counted as duplicate)
        """
        url = reverse("digid-mock:password")

        # create profile
        params = {
            "acs": reverse("acs"),
            "next": reverse("profile:registration_necessary"),
        }
        url = f"{url}?{urlencode(params)}"

        data = {
            "auth_name": "533458225",
            "auth_pass": "bar",
        }
        # post our password to the IDP
        response = self.app.post(url, data).follow().follow()

        form = response.forms["necessary-form"]
        form["email"] = "test@example.com"
        form["first_name"] = "original_first"
        form["last_name"] = "original_last"
        response = form.submit().follow()

        user = User.objects.get(email="test@example.com")

        self.assertEqual(user.first_name, "original_first")
        self.assertEqual(user.last_name, "original_last")

        # edit profile
        url = reverse("profile:edit")

        edit_page = self.app.get(url, user=user)

        form = edit_page.forms["profile-edit"]
        form["first_name"] = "changed_first"
        form["last_name"] = "changed_last"
        response = form.submit()

        user.refresh_from_db()

        self.assertEqual(user.first_name, "changed_first")
        self.assertEqual(user.last_name, "changed_last")

    #
    # non-digid users
    #
    def test_non_digid_user_fail(self):
        """Assert that non-digid users cannot register with duplicate emails"""

        url = reverse("django_registration_register")

        test_user = User.objects.create(email="test@example.com")

        # enable login with email + password
        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

        register_page = self.app.get(url)
        form = register_page.forms["registration-form"]
        form["email"] = test_user.email
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["password1"] = "SomePassword123"
        form["password2"] = "SomePassword123"

        response = form.submit()

        expected_errors = {"email": [self.msg_dupes]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

        users = User.objects.filter(email=test_user.email)

        self.assertEqual(users.count(), 1)

    def test_non_digid_user_case_sensitive_duplicate_fail(self):
        """
        Assert that non-digid users cannot register with emails that differ from
        existing emails only in case
        """
        url = reverse("django_registration_register")

        User.objects.create(email="test@example.com")

        # enable login with email + password
        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

        register_page = self.app.get(url)
        form = register_page.forms["registration-form"]
        form["email"] = "TEST@example.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["password1"] = "SomePassword123"
        form["password2"] = "SomePassword123"

        response = form.submit()

        self.assertEqual(response.status_code, 200)

        expected_errors = {"email": [self.msg_dupes]}

        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_non_digid_user_inactive_duplicates_fail(self):
        """Assert that non-digid users cannot register with inactive duplicate emails"""

        url = reverse("django_registration_register")

        # enable login with email + password
        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

        inactive_user = UserFactory.create(is_active=False)

        register_page = self.app.get(url)
        form = register_page.forms["registration-form"]
        form["email"] = inactive_user.email
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["password1"] = "SomePassword123"
        form["password2"] = "SomePassword123"

        response = form.submit()

        expected_errors = {"email": [self.msg_dupes]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors, expected_errors)

    def test_non_digid_user_can_edit_profile(self):
        """
        Assert that non-digid users can edit their profile (the email of the same user
        is not counted as duplicate)
        """

        url = reverse("profile:edit")
        test_user = User.objects.create(
            email="test@example.com",
        )

        edit_page = self.app.get(url, user=test_user)

        form = edit_page.forms["profile-edit"]
        form["first_name"] = "changed_first"
        form["last_name"] = "changed_last"
        form.submit()

        user = User.objects.get(id=test_user.id)

        self.assertEqual(user.first_name, "changed_first")
        self.assertEqual(user.last_name, "changed_last")


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestRegistrationNecessary(ClearCachesMixin, WebTest):
    url = reverse_lazy("profile:registration_necessary")

    @classmethod
    def setUpTestData(cls):
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)

    def test_page_show_config_text(self):
        config = SiteConfiguration.get_solo()
        config.registration_text = "Hello registration text http://foo.bar/"
        config.save()

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        self.assertContains(response, "Hello registration text")
        self.assertContains(response, ' href="http://foo.bar/" ')

    def test_any_page_for_digid_user_redirect_to_necessary_fields(self):
        user = NewDigidUserFactory()
        urls = [
            reverse("pages-root"),
            reverse("products:category_list"),
            reverse("cases:index"),
            reverse("profile:detail"),
            reverse("profile:data"),
            reverse("collaborate:plan_list"),
            reverse("general_faq"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.app.get(url, user=user)

                redirect = furl(reverse("profile:registration_necessary"))
                if url != reverse("pages-root"):
                    redirect.set({"next": url})

                self.assertRedirects(response, redirect.url)

    def test_submit_without_invite(self):
        config = SiteConfiguration.get_solo()
        config.notifications_cases_enabled = True
        config.enable_notification_channel_choice = True
        config.save()

        user = UserFactory(
            first_name="",
            last_name="",
            email="test@example.org",
            login_type=LoginTypeChoices.digid,
        )
        self.assertTrue(user.require_necessary_fields())

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

        # check email is not prefilled
        self.assertEqual(form["email"].value, "")

        form["email"] = "john@smith.com"
        form["first_name"] = "John"
        form["last_name"] = "Smith"
        form["case_notification_channel"] = NotificationChannelChoice.digital_only

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pages-root"))

        user.refresh_from_db()

        self.assertFalse(user.require_necessary_fields())
        self.assertEqual(user.email, "john@smith.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Smith")

    def test_submit_with_invite(self):
        user = UserFactory()
        contact = UserFactory.build(email="test@example.org")
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
        self.assertEqual(response.url, reverse("pages-root"))

        user_contact = User.objects.get(email=contact.email)
        invite.refresh_from_db()

        self.assertEqual(user_contact.first_name, contact.first_name)
        self.assertEqual(user_contact.last_name, contact.last_name)
        self.assertEqual(user_contact.email, contact.email)
        self.assertEqual(list(user.user_contacts.all()), [user_contact])

    #     def test_non_unique_email_fails(self):
    #         UserFactory.create(email="john@smith.com")
    #         user = UserFactory.create(
    #             first_name="",
    #             last_name="",
    #             login_type=LoginTypeChoices.digid,
    #         )

    #         response = self.app.get(self.url, user=user)
    #         form = response.forms["necessary-form"]

    #         form["email"] = "john@smith.com"
    #         form["first_name"] = "John"
    #         form["last_name"] = "Smith"

    #         response = form.submit()

    #         self.assertEqual(response.status_code, 200)

    #         expected_errors = {
    #             "email": [
    #                 _(
    #                     "A user with this Email already exists. If you need to register "
    #                     "with an Email addresss that is already in use, both users of the "
    #                     "address need to be registered with login type DigiD."
    #                 )
    #             ]
    #         }
    #         self.assertEqual(response.context["form"].errors, expected_errors)

    #     def test_non_unique_email_case_sensitive_fails(self):
    #         UserFactory.create(email="john@example.com")
    #         user = UserFactory.create(
    #             first_name="",
    #             last_name="",
    #             login_type=LoginTypeChoices.digid,
    #         )

    #         response = self.app.get(self.url, user=user)
    #         form = response.forms["necessary-form"]

    #         form["email"] = "John@example.com"
    #         form["first_name"] = "John"
    #         form["last_name"] = "Smith"

    #         response = form.submit()

    #         self.assertEqual(response.status_code, 200)

    #         expected_errors = {
    #             "email": [
    #                 _(
    #                     "A user with this Email already exists. If you need to register "
    #                     "with an Email addresss that is already in use, both users of the "
    #                     "address need to be registered with login type DigiD."
    #                 )
    #             ]
    #         }
    #         self.assertEqual(response.context["form"].errors, expected_errors)

    def test_submit_invalid_first_name_chars_fails(self):
        UserFactory.create(email="john@smith.com")
        user = UserFactory.create(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        invalid_characters = '<>#/"\\,.:;'

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["email"] = "user@example.com"
                form["first_name"] = char
                form["last_name"] = "Smith"
                response = form.submit()
                expected_errors = {
                    "first_name": [
                        _(
                            "Please make sure your input contains only valid characters "
                            "(letters, numbers, apostrophe, dash, space)."
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
        invalid_characters = '<>#/"\\,.:;'

        response = self.app.get(self.url, user=user)
        form = response.forms["necessary-form"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["email"] = "user@example.com"
                form["first_name"] = "John"
                form["last_name"] = char
                response = form.submit()
                expected_errors = {
                    "last_name": [
                        _(
                            "Please make sure your input contains only valid characters "
                            "(letters, numbers, apostrophe, dash, space)."
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestLoginLogoutFunctionality(AssertRedirectsMixin, WebTest):
    def setUp(self):
        # Create a user. We need to reset their password
        # because otherwise we do not have access to the raw one associated.
        self.user = UserFactory.create(password="test")

        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

    def test_login_page_has_next_url(self):
        response = self.app.get(reverse("profile:contact_list"))
        self.assertRedirects(
            response,
            furl(reverse("login")).add({"next": reverse("profile:contact_list")}).url,
        )
        self.assertIn(
            furl("").add({"next": reverse("profile:contact_list")}).url,
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

    @patch("open_inwoner.accounts.gateways.gateway.send")
    @freeze_time("2023-05-22 12:05:01")
    def test_regular_login_with_valid_credentials_triggers_the_2fa_flow(
        self, mock_gateway_send
    ):
        config = SiteConfiguration.get_solo()
        config.login_2fa_sms = True
        config.save()

        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        login_form = response.forms["login-form"]
        login_form["username"] = self.user.email
        login_form["password"] = "test"
        login_form_response = login_form.submit()
        login_form_response.follow()

        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)

        params = {
            "next": "",
            "user": TimestampSigner().sign(self.user.pk),
        }
        verify_token_url = furl(reverse("verify_token")).add(params).url
        self.assertRedirects(login_form_response, verify_token_url)
        self.assertNotIn(
            "_auth_user_id",
            self.app.session,
            msg="Valid credentials alone should not authenticate a user, second factor required",
        )

    def test_login_page_shows_correct_digid_login_url(self):
        config = OpenIDDigiDConfig.get_solo()

        for oidc_enabled in [True, False]:
            with self.subTest(oidc_enabled=oidc_enabled):
                config.enabled = oidc_enabled
                config.save()

                login_url = (
                    f"{reverse('digid_oidc:init')}?next="
                    if oidc_enabled
                    else f"{reverse('digid:login')}?next="
                )

                response = self.app.get(reverse("login"))

                digid_login_title = _("Inloggen met DigiD")
                digid_login_link = response.pyquery(f"[title='{digid_login_title}']")

                self.assertEqual(digid_login_link.attr("href"), login_url)

    def test_login_page_shows_correct_eherkenning_login_url(self):
        site_config = SiteConfiguration.get_solo()
        site_config.eherkenning_enabled = True
        site_config.save()

        config = OpenIDEHerkenningConfig.get_solo()

        for oidc_enabled in [True, False]:
            with self.subTest(oidc_enabled=oidc_enabled):
                config.enabled = oidc_enabled
                config.save()

                login_url = (
                    f"{reverse('eherkenning_oidc:init')}?next="
                    if oidc_enabled
                    else f"{reverse('eherkenning:login')}?next="
                )

                response = self.app.get(reverse("login"))

                eherkenning_login_title = _("Inloggen met eHerkenning")
                eherkenning_login_link = response.pyquery(
                    f"[title='{eherkenning_login_title}']"
                )

                self.assertEqual(eherkenning_login_link.attr("href"), login_url)

    def test_login_for_inactive_user_shows_appropriate_message(self):
        # Change user to inactive
        self.user.is_active = False
        self.user.save()

        form = self.app.get(reverse("login")).forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "test"
        response = form.submit()

        self.assertEqual(
            response.context["errors"],
            [
                _(
                    "Voer een juiste E-mailadres en wachtwoord in. Let op dat beide velden hoofdlettergevoelig zijn."
                )
            ],
        )

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
        self.assertRedirects(logout_response, reverse("login"))
        self.assertFalse(logout_response.follow().context["user"].is_authenticated)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestPasswordResetFunctionality(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()

    def test_password_reset_form_custom_template_is_rendered(self):
        response = self.app.get(reverse("password_reset"))
        self.assertContains(response, _("Reset password"))

    def test_password_reset_email_contains_proper_data(self):
        current_site = Site.objects.get_current()
        self.app.post(reverse("password_reset"), {"email": self.user.email})
        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        body = sent_mail.body
        self.assertEqual(
            _("Password reset for {domain}").format(domain=current_site.name),
            sent_mail.subject,
        )
        self.assertIn(
            _(
                "U ontvangt deze e-mail, omdat u een aanvraag voor opnieuw instellen van het wachtwoord voor uw account op example.com hebt gedaan."
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
        self.assertContains(confirm_response, _("Change my password"))

    def test_custom_password_reset_form_sends_email_when_user_is_default(self):
        self.app.post(reverse("password_reset"), {"email": self.user.email})
        self.assertEqual(len(mail.outbox), 1)

    def test_custom_password_reset_form_does_not_send_email_when_user_is_digid(self):
        digid_user = UserFactory(
            login_type=LoginTypeChoices.digid, email="john@smith.nl"
        )
        self.app.post(reverse("password_reset"), {"email": digid_user.email})
        self.assertEqual(len(mail.outbox), 0)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestPasswordChange(WebTest):
    def setUp(self):
        self.user = UserFactory()

    def test_password_change_form_custom_template_is_rendered(self):
        response = self.app.get(reverse("password_change"), user=self.user)
        self.assertContains(response, _("Password reset"))

    def test_password_change_form_done_custom_template_is_rendered(self):
        response = self.app.get(reverse("password_change_done"), user=self.user)
        self.assertContains(response, _("Your password has been changed."))

    def test_password_change_button_is_rendered_with_default_login_type(self):
        response = self.app.get(reverse("profile:detail"), user=self.user)

        doc = PQ(response.content)
        link = doc.find("[aria-label='Wachtwoord']")[0]
        self.assertTrue(doc(link).is_("a"))

    def test_password_change_button_is_not_rendered_with_digid_login_type(self):
        digid_user = UserFactory(
            login_type=LoginTypeChoices.digid, email="john@smith.nl"
        )
        response = self.app.get(reverse("profile:detail"), user=digid_user)

        doc = PQ(response.content)
        links = doc.find("[aria-label='Wachtwoord']")
        self.assertEqual(len(links), 0)

    def test_anonymous_user_is_redirected_to_login_page_if_password_change_is_accessed(
        self,
    ):
        response = self.app.get(reverse("password_change"))
        expected_url = (
            furl(reverse("login")).add({"next": reverse("password_change")}).url
        )
        self.assertRedirects(response, expected_url)


@requests_mock.Mocker()
class UpdateUserOnLoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        MockAPIReadPatchData.setUpServices()
        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = True
        config.save()

    def test_update_hook_is_registered_on_login(self, m):
        connected_functions = [receiver[1]() for receiver in user_logged_in.receivers]
        self.assertIn(update_user_on_login, connected_functions)

    def test_update_hook_not_called(self, m):
        self.data = MockAPIReadPatchData().install_mocks(m)
        request = RequestFactory().get("/foo")
        request.user = self.data.user

        for login_type in [LoginTypeChoices.default, LoginTypeChoices.oidc]:
            with self.subTest(f"{login_type}"):
                self.data.user.login_type = login_type
                self.data.user.save()

                update_user_on_login(
                    self.__class__,
                    request.user,
                    request,
                )

                with patch(
                    "open_inwoner.openklant.services.eSuiteKlantenService.update_user_from_klant"
                ) as update_user_mock:
                    update_user_mock.assert_not_called()

    def test_digid_user_update_hook_called(self, m):
        self.data = MockAPIReadPatchData().install_mocks(m)
        request = RequestFactory().get("/foo")
        request.user = self.data.user

        self.data.user.login_type = LoginTypeChoices.digid
        self.data.user.save()
        with patch(
            "open_inwoner.openklant.services.eSuiteKlantenService.update_user_from_klant"
        ) as update_user_mock:
            update_user_on_login(
                self.__class__,
                request.user,
                request,
            )
            update_user_mock.assert_called_once()

    def test_update_eherkenning_user(self, m):
        self.data = MockAPIReadPatchData().install_mocks(m)
        request = RequestFactory().get("/foo")
        request.user = self.data.user

        self.data.user.login_type = LoginTypeChoices.eherkenning
        self.data.user.save()

        self.assertEqual(request.user.company_name, "")

        vestiging = {
            "kvkNummer": "68750110",
            "vestigingsnummer": "000037178598",
            "naam": "Test BV Donald",
            "adres": {
                "binnenlandsAdres": {
                    "type": "bezoekadres",
                    "straatnaam": "Hizzaarderlaan",
                    "plaats": "Lollum",
                }
            },
            "type": "hoofdvestiging",
            "_links": {
                "basisprofiel": {
                    "href": "https://api.kvk.nl/test/api/v1/basisprofielen/68750110"
                },
                "vestigingsprofiel": {
                    "href": "https://api.kvk.nl/test/api/v1/vestigingsprofielen/000037178598"
                },
            },
        }

        with patch.object(KvKClient, "get_company_headquarters") as mock_kvk:
            mock_kvk.return_value = vestiging
            update_user_on_login(
                self.__class__,
                request.user,
                request,
            )

            mock_kvk.assert_called_once()

        self.assertEqual(request.user.company_name, "Test BV Donald")
