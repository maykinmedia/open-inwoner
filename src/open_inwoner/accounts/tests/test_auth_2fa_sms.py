import datetime
import time
from unittest.mock import ANY, patch

from django.conf import settings
from django.core.signing import TimestampSigner
from django.test import override_settings
from django.test.utils import freeze_time as dj_freeze_time
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from django_webtest import WebTest
from freezegun import freeze_time
from furl import furl
from timeline_logger.models import TimelineLog

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.logentry import LOG_ACTIONS
from open_inwoner.utils.validators import format_phone_number

from ..gateways import GatewayError
from .factories import UserFactory

signer = TimestampSigner()


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestSMSVerificationLogin(WebTest):
    def setUp(self):
        self.user = UserFactory(email="ex@example.com", password="secret")

        self.config = SiteConfiguration.get_solo()
        self.config.login_2fa_sms = True
        self.config.login_allow_registration = True
        self.config.save()

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_regular_login_with_2fa_disabled(self, mock_gateway_send):
        self.config.login_2fa_sms = False
        self.config.save()

        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        login_form = response.forms["login-form"]
        login_form["username"] = self.user.email
        login_form["password"] = "secret"
        login_form_response = login_form.submit()
        login_form_response_redirect = login_form_response.follow()

        mock_gateway_send.assert_not_called()
        self.assertRedirects(login_form_response, reverse("pages-root"))
        self.assertNotContains(login_form_response_redirect, "Account verificatie")

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_with_valid_token_succeeds(self, mock_gateway_send):
        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        login_form = response.forms["login-form"]
        login_form["username"] = self.user.email
        login_form["password"] = "secret"
        response = login_form.submit()
        response_redirect = response.follow()

        self.assertContains(response_redirect, _("Account verificatie"))
        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)

        sent_token = mock_gateway_send.call_args[1]["token"]

        verify_token_form = response_redirect.forms["verify-token-form"]
        verify_token_form["token"] = sent_token
        response = verify_token_form.submit()

        self.assertRedirects(response, reverse("pages-root"))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_with_invalid_token_fails(self, mock_gateway_send):
        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        login_form = response.forms["login-form"]
        login_form["username"] = self.user.email
        login_form["password"] = "secret"
        response = login_form.submit()
        response_redirect = response.follow()

        self.assertContains(response_redirect, _("Account verificatie"))
        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)

        verify_token_form = response_redirect.forms["verify-token-form"]
        verify_token_form["token"] = "wrongt"
        response = verify_token_form.submit()

        self.assertEqual(
            response.context["form"].errors,
            {"token": [_("De opgegeven code is ongeldig of is verlopen.")]},
        )

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_fails_with_sms_failure(self, mock_gateway_send):
        mock_gateway_send.side_effect = GatewayError

        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        login_form = response.forms["login-form"]
        login_form["username"] = self.user.email
        login_form["password"] = "secret"
        response = login_form.submit()
        response_redirect = response.follow()

        self.assertEqual(
            [str(m) for m in response_redirect.context["messages"]],
            [
                _(
                    "Het is vanwege een storing tijdelijk niet mogelijk om in te loggen, probeer het over 15 minuten nogmaals. "
                    "Mocht het inloggen na meerdere pogingen niet werken, neem dan contact op met de Open Inwoner Platform."
                )
            ],
        )

        log_entry = TimelineLog.objects.last()

        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _(
                    "Het versturen van een SMS-bericht aan {phonenumber} is mislukt. Inloggen afgebroken."
                ).format(phonenumber=self.user.phonenumber),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    @patch("open_inwoner.accounts.gateways.gateway.send")
    @override_settings(ACCOUNTS_USER_TOKEN_EXPIRE_TIME=300)
    def test_login_fails_with_token_timeout(self, mock_gateway_send):
        with freeze_time("2023-05-22 11:00:00"):
            response = self.app.get(reverse("login"))
            mock_gateway_send.assert_not_called()

            login_form = response.forms["login-form"]
            login_form["username"] = self.user.email
            login_form["password"] = "secret"
            response = login_form.submit()
            response_redirect = response.follow()

            self.assertContains(response_redirect, _("Account verificatie"))
            mock_gateway_send.assert_called_once_with(
                to=self.user.phonenumber, token=ANY
            )

            sent_token = mock_gateway_send.call_args[1]["token"]

        with freeze_time("2023-05-22 11:05:01"):
            verify_token_form = response_redirect.forms["verify-token-form"]
            verify_token_form["token"] = sent_token
            response = verify_token_form.submit()

            self.assertRedirects(response, reverse("login"))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_token_with_max_attempts(self, mock_gateway_send):
        with freeze_time("2023-05-22 12:00:00") as frozen_time:
            response = self.app.get(reverse("login"))
            mock_gateway_send.assert_not_called()

            # login form
            login_form = response.forms["login-form"]
            login_form["username"] = self.user.email
            login_form["password"] = "secret"
            user1_login_response = login_form.submit()

            user1_verify_token_response = user1_login_response.follow()

            self.assertContains(user1_verify_token_response, _("Account verificatie"))

            user1_sent_token = mock_gateway_send.call_args[1]["token"]

            # we have an amount of 3 visits per minute so we should get
            # the warning on the fourth attempt
            for visit in range(1, 5):
                user1_verify_token_form = user1_verify_token_response.forms[
                    "verify-token-form"
                ]
                user1_verify_token_form["token"] = "wrongt"
                user1_verify_response = user1_verify_token_form.submit(status=200)

            self.assertContains(
                user1_verify_response,
                "Maximaal 3 pogingen. Probeer het over 1 minuut opnieuw",
            )

            # try again after 1 minute
            frozen_time.tick(delta=datetime.timedelta(minutes=1))
            user1_verify_token_form["token"] = user1_sent_token
            user1_verify_response5 = user1_verify_token_form.submit()

            self.assertRedirects(user1_verify_response5, reverse("pages-root"))

            # check a new user can log in
            frozen_time.tick(delta=datetime.timedelta(minutes=-1))
            other_user = UserFactory(email="ex2@example.com", password="secret2")

            response = self.app.get(reverse("login"))
            login_form = response.forms["login-form"]
            login_form["username"] = other_user.email
            login_form["password"] = "secret2"
            response = login_form.submit()
            response_redirect = response.follow()

            self.assertContains(response_redirect, _("Account verificatie"))
            mock_gateway_send.assert_called()
            self.assertEqual(mock_gateway_send.call_count, 2)
            self.assertEqual(
                mock_gateway_send.call_args[1]["to"], other_user.phonenumber
            )

            sent_token = mock_gateway_send.call_args[1]["token"]

            verify_token_form = response_redirect.forms["verify-token-form"]
            verify_token_form["token"] = sent_token
            response = verify_token_form.submit()

            self.assertRedirects(response, reverse("pages-root"))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    @freeze_time("2023-05-22 12:00:00")
    def test_login_when_resending_sms(self, mock_gateway_send):
        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        login_form = response.forms["login-form"]
        login_form["username"] = self.user.email
        login_form["password"] = "secret"
        login_response = login_form.submit()
        login_response_redirect = login_response.follow()

        params = {
            "next": "",
            "user": signer.sign(self.user.pk),
        }
        verify_token_url = furl(reverse("verify_token")).add(params).url

        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)
        self.assertRedirects(login_response, verify_token_url)
        self.assertContains(login_response_redirect, _("Account verificatie"))

        response = self.client.post(
            furl(reverse("resend_token")).add(params).url,
            follow=True,
            HTTP_REFERER=verify_token_url,
        )

        mock_gateway_send.assert_called_with(to=self.user.phonenumber, token=ANY)
        self.assertEqual(mock_gateway_send.call_count, 2)
        self.assertRedirects(response, furl(reverse("verify_token")).add(params).url)

        sent_token = mock_gateway_send.call_args[1]["token"]

        verify_token_form = login_response_redirect.forms["verify-token-form"]
        verify_token_form["token"] = sent_token
        response = verify_token_form.submit()

        self.assertRedirects(response, reverse("pages-root"))

    @patch(
        "open_inwoner.accounts.views.login.ResendTokenView.throttle_visits",
        new_callable=lambda: 2,
    )
    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_resend_sms_max_attempts(
        self, mock_gateway_send, mock_login_throttle_visits
    ):
        with freeze_time("2023-05-22 12:00:00"):
            response = self.app.get(reverse("login"))
            mock_gateway_send.assert_not_called()

            login_form = response.forms["login-form"]
            login_form["username"] = self.user.email
            login_form["password"] = "secret"
            login_response = login_form.submit()
            login_response_redirect = login_response.follow()

            params = {
                "next": "",
                "user": signer.sign(self.user.pk),
            }

            mock_gateway_send.assert_called_once_with(
                to=self.user.phonenumber, token=ANY
            )
            verify_token_url = furl(reverse("verify_token")).add(params).url

            self.assertRedirects(login_response, verify_token_url)
            self.assertContains(login_response_redirect, _("Account verificatie"))

            resend_token_url = furl(reverse("resend_token")).add(params).url
            # we have a limit of 25 visit times per 5 minutes
            # here we have limited this to 2 times for testing purposes
            for login_attempt in range(1, 3):
                with self.subTest(login_attempt=login_attempt):
                    response = self.client.post(
                        path=resend_token_url,
                        follow=True,
                        HTTP_REFERER=verify_token_url,
                    )

                    mock_gateway_send.assert_called_with(
                        to=self.user.phonenumber, token=ANY
                    )
                    self.assertEqual(mock_gateway_send.call_count, login_attempt + 1)
                    self.assertRedirects(response, verify_token_url)

            response = self.client.post(
                path=resend_token_url,
                follow=True,
                HTTP_REFERER=verify_token_url,
            )

            self.assertEqual(response.status_code, 403)
            self.assertEqual(mock_gateway_send.call_count, 3)

        # new attempt 5 minutes later
        with freeze_time("2023-05-22 12:05:01"):
            response = self.app.get(reverse("login"))
            login_form = response.forms["login-form"]
            login_form["username"] = self.user.email
            login_form["password"] = "secret"
            login_response = login_form.submit()
            login_response_redirect = login_response.follow()

            params = {
                "next": "",
                "user": signer.sign(self.user.pk),
            }

            verify_token_url = furl(reverse("verify_token")).add(params).url

            self.assertRedirects(login_response, verify_token_url)
            self.assertContains(login_response_redirect, _("Account verificatie"))
            self.assertEqual(mock_gateway_send.call_count, 4)
            mock_gateway_send.assert_called_with(to=self.user.phonenumber, token=ANY)

            resend_token_url = furl(reverse("resend_token")).add(params).url

            # Unblocked attempt.
            response = self.client.post(
                path=resend_token_url,
                follow=True,
                HTTP_REFERER=verify_token_url,
            )

            self.assertEqual(mock_gateway_send.call_count, 5)
            self.assertRedirects(response, verify_token_url)
            mock_gateway_send.assert_called_with(to=self.user.phonenumber, token=ANY)

    @override_settings(ACCOUNTS_USER_TOKEN_EXPIRE_TIME=150)
    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_resend_sms_user_token_expires(self, mock_gateway_send):
        now = timezone.now()
        some_time_ago = now - datetime.timedelta(seconds=151)

        # freezegun's freeze_time does not work well with time.time,
        # so we are using django's decorator instead.
        with dj_freeze_time(time.mktime(some_time_ago.timetuple())):
            params = {
                "next": "",
                "user": signer.sign(self.user.pk),
            }

        verify_token_url = furl(reverse("verify_token")).add(params).url
        response = self.client.post(
            furl(reverse("resend_token")).add(params).url,
            follow=True,
            HTTP_REFERER=verify_token_url,
        )

        self.assertRedirects(response, str(settings.LOGIN_URL))
        mock_gateway_send.assert_not_called()

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_by_adding_phone_number_succeeds(self, mock_gateway_send):
        self.user.phonenumber = ""
        self.user.save()

        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        form = response.forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "secret"
        login_response = form.submit()
        login_response_redirect = login_response.follow()

        self.assertContains(
            login_response_redirect, _("Account verificatie (stap 1 van 2)")
        )
        mock_gateway_send.assert_not_called()

        phonenumber1_form = login_response_redirect.forms["add-phonenumber-1-form"]
        phonenumber1_form["phonenumber-phonenumber_1"] = "0643465651"
        phonenumber1_form["phonenumber-phonenumber_2"] = "0643465651"
        phonenumber1_response = phonenumber1_form.submit()

        self.assertContains(phonenumber1_response, "Account verificatie (stap 2 van 2)")
        mock_gateway_send.assert_called_with(
            to=format_phone_number("0643465651"), token=ANY
        )

        sent_token = mock_gateway_send.call_args[1]["token"]

        phonenumber2_form = phonenumber1_response.forms["add-phonenumber-2-form"]
        phonenumber2_form["verify-token"] = sent_token
        phonenumber2_response = phonenumber2_form.submit()

        self.user.refresh_from_db()

        self.assertEqual(self.user.phonenumber, "+31643465651")
        self.assertRedirects(phonenumber2_response, str(settings.LOGIN_REDIRECT_URL))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_fails_with_different_phonenumbers(self, mock_gateway_send):
        self.user.phonenumber = ""
        self.user.save()

        response = self.app.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        form = response.forms["login-form"]
        form["username"] = self.user.email
        form["password"] = "secret"
        login_response_redirect = form.submit().follow()

        self.assertContains(
            login_response_redirect, _("Account verificatie (stap 1 van 2)")
        )
        mock_gateway_send.assert_not_called()

        phonenumber_form = login_response_redirect.forms["add-phonenumber-1-form"]
        phonenumber_form["phonenumber-phonenumber_1"] = "0643465651"
        phonenumber_form["phonenumber-phonenumber_2"] = "0643775651"
        phonenumber_response = phonenumber_form.submit()

        self.assertEqual(
            phonenumber_response.context["form"].errors,
            {"__all__": [_("De telefoonnummers komen niet overeen.")]},
        )
