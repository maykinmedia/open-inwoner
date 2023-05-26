import datetime
import time
from unittest.mock import ANY, patch

from django.conf import settings
from django.core.signing import TimestampSigner
from django.test import TestCase, override_settings
from django.test.utils import freeze_time as dj_freeze_time
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.logentry import LOG_ACTIONS
from open_inwoner.utils.validators import format_phone_number

from ..gateways import GatewayError
from .factories import UserFactory

signer = TimestampSigner()


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestSMSVerificationLogin(TestCase):
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

        response = self.client.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=True,
        )

        self.assertNotContains(response, "Account verificatie")
        self.assertRedirects(response, reverse("pages-root"))
        mock_gateway_send.assert_not_called()

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_with_valid_token_succeeds(self, mock_gateway_send):
        response = self.client.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=True,
        )

        self.assertContains(response, _("Account verificatie"))
        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)

        sent_token = mock_gateway_send.call_args[1]["token"]

        response = self.client.post(
            response._request.get_full_path(),
            follow=True,
            data={
                "token": sent_token,
            },
        )

        self.assertRedirects(response, reverse("pages-root"))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_with_invalid_token_fails(self, mock_gateway_send):
        response = self.client.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=True,
        )

        self.assertContains(response, _("Account verificatie"))
        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)

        response = self.client.post(
            response._request.get_full_path(),
            follow=True,
            data={
                "token": "wromgt",
            },
        )

        self.assertEqual(
            response.context["form"].errors,
            {"token": [_("De opgegeven code is ongeldig of is verlopen.")]},
        )

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_fails_with_sms_failure(self, mock_gateway_send):
        mock_gateway_send.side_effect = GatewayError

        response = self.client.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=False,
        )

        self.assertEqual(response.url, reverse("pages-root"))

        response = self.client.get(response.url, follow=True)

        self.assertEqual(
            [str(m) for m in response.context["messages"]],
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
            response = self.client.get(reverse("login"))
            mock_gateway_send.assert_not_called()

            response = self.client.post(
                reverse("login"),
                data={
                    "next": "",
                    "username": self.user.email,
                    "password": "secret",
                },
                follow=True,
            )

            self.assertContains(response, _("Account verificatie"))
            mock_gateway_send.assert_called_once_with(
                to=self.user.phonenumber, token=ANY
            )

            sent_token = mock_gateway_send.call_args[1]["token"]

        with freeze_time("2023-05-22 11:05:10"):
            response = self.client.post(
                response._request.get_full_path(),
                data={
                    "token": sent_token,
                },
            )

            self.assertRedirects(response, reverse("login"))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_token_with_max_attempts(self, mock_gateway_send):
        with freeze_time("2023-05-22 12:00:00"):
            response = self.client.get(reverse("login"))
            mock_gateway_send.assert_not_called()

            response = self.client.post(
                reverse("login"),
                data={
                    "next": "",
                    "username": self.user.email,
                    "password": "secret",
                },
                follow=True,
            )

            self.assertContains(response, _("Account verificatie"))

            user_1_token_post_path = response._request.get_full_path()
            user_1_sent_token = mock_gateway_send.call_args[1]["token"]

            # we have an amount of 3 visits per minute so we should get
            # the warning on the fourth attempt
            for i in range(1, 5):
                response = self.client.post(
                    response._request.get_full_path(),
                    follow=True,
                    data={
                        "token": "wrongt",
                    },
                )
                self.assertEqual(response.status_code, 200)

            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response, "Maximaal 3 pogingen. Probeer het over 1 minuut opnieuw"
            )

            # check with a new user
            other_user = UserFactory(email="ex2@example.com", password="secret2")
            response = self.client.post(
                reverse("login"),
                data={
                    "next": "",
                    "username": other_user.email,
                    "password": "secret2",
                },
                follow=True,
            )

            self.assertContains(response, _("Account verificatie"))
            mock_gateway_send.assert_called()
            self.assertEqual(mock_gateway_send.call_count, 2)
            self.assertEqual(
                mock_gateway_send.call_args[1]["to"], other_user.phonenumber
            )

            sent_token = mock_gateway_send.call_args[1]["token"]

            response = self.client.post(
                response._request.get_full_path(),
                follow=True,
                data={
                    "token": sent_token,
                },
            )
            other_user.refresh_from_db()
            self.assertRedirects(response, reverse("pages-root"))

        # make sure the first user can login after a minute has passed
        with freeze_time("2023-05-22 12:01:01"):
            response = self.client.post(
                user_1_token_post_path,
                follow=True,
                data={
                    "token": user_1_sent_token,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertRedirects(response, reverse("pages-root"))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    @freeze_time("2023-05-22 12:00:00")
    def test_login_when_resending_sms(self, mock_gateway_send):
        response = self.client.get(reverse("login"))
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=True,
        )

        params = {
            "next": "",
            "user": signer.sign(self.user.pk),
        }

        mock_gateway_send.assert_called_once_with(to=self.user.phonenumber, token=ANY)
        self.assertRedirects(
            response, reverse("verify_token") + "?" + urlencode(params)
        )
        self.assertContains(response, _("Account verificatie"))

        location = reverse("verify_token") + "?" + urlencode(params)
        response = self.client.post(
            reverse("resend_token") + "?" + urlencode(params),
            follow=True,
            HTTP_REFERER=location,
        )

        mock_gateway_send.assert_called_with(to=self.user.phonenumber, token=ANY)
        self.assertEqual(mock_gateway_send.call_count, 2)
        self.assertRedirects(
            response, reverse("verify_token") + "?" + urlencode(params)
        )

        sent_token = mock_gateway_send.call_args[1]["token"]

        response = self.client.post(
            response._request.get_full_path(),
            follow=True,
            data={
                "token": sent_token,
            },
        )
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
            response = self.client.get(reverse("login"))
            mock_gateway_send.assert_not_called()

            response = self.client.post(
                reverse("login"),
                data={
                    "next": "",
                    "username": self.user.email,
                    "password": "secret",
                },
                follow=True,
            )

            params = {
                "next": "",
                "user": signer.sign(self.user.pk),
            }

            mock_gateway_send.assert_called_once_with(
                to=self.user.phonenumber, token=ANY
            )
            self.assertRedirects(
                response, f"{reverse('verify_token')}?{urlencode(params)}"
            )
            self.assertContains(response, _("Account verificatie"))

            location = reverse("verify_token") + "?" + urlencode(params)

            # we have a limit of 25 visit times per 5 minutes
            # here we have limited this to 2 times for testing purposes
            for login_attempt in range(1, 3):
                with self.subTest(login_attempt=login_attempt):
                    response = self.client.post(
                        path=f"{reverse('resend_token')}?{urlencode(params)}",
                        follow=True,
                        HTTP_REFERER=location,
                    )

                    mock_gateway_send.assert_called_with(
                        to=self.user.phonenumber, token=ANY
                    )
                    self.assertEqual(mock_gateway_send.call_count, login_attempt + 1)
                    self.assertRedirects(
                        response, f"{reverse('verify_token')}?{urlencode(params)}"
                    )

            response = self.client.post(
                path=f"{reverse('resend_token')}?{urlencode(params)}",
                follow=True,
                HTTP_REFERER=location,
            )

            self.assertEqual(response.status_code, 403)
            self.assertEqual(mock_gateway_send.call_count, 3)

        # new attempt 5 minutes later
        with freeze_time("2023-05-22 12:05:01"):
            response = self.client.post(
                reverse("login"),
                data={
                    "next": "",
                    "username": self.user.email,
                    "password": "secret",
                },
                follow=True,
            )

            params = {
                "next": "",
                "user": signer.sign(self.user.pk),
            }

            self.assertRedirects(
                response, f"{reverse('verify_token')}?{urlencode(params)}"
            )
            self.assertContains(response, _("Account verificatie"))
            self.assertEqual(mock_gateway_send.call_count, 4)
            mock_gateway_send.assert_called_with(to=self.user.phonenumber, token=ANY)

            # Unblocked attempt.
            location = f"{reverse('verify_token')}?{urlencode(params)}"
            response = self.client.post(
                path=f"{reverse('resend_token')}?{urlencode(params)}",
                follow=True,
                HTTP_REFERER=location,
            )

            self.assertEqual(mock_gateway_send.call_count, 5)
            self.assertRedirects(
                response, f"{reverse('verify_token')}?{urlencode(params)}"
            )
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

        location = reverse("verify_token") + "?" + urlencode(params)
        response = self.client.post(
            reverse("resend_token") + "?" + urlencode(params),
            follow=True,
            HTTP_REFERER=location,
        )

        self.assertRedirects(response, str(settings.LOGIN_URL))
        mock_gateway_send.assert_not_called()

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_by_adding_phone_number_succeeds(self, mock_gateway_send):
        self.user.phonenumber = ""
        self.user.save()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=True,
        )

        self.assertContains(response, "Account verificatie (stap 1 van 2)")
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            response._request.get_full_path(),
            data={
                "add_phone_number_wizard_view-current_step": "phonenumber",
                "phonenumber-phonenumber_1": "0643465651",
                "phonenumber-phonenumber_2": "0643465651",
            },
            follow=True,
        )

        self.assertContains(response, "Account verificatie (stap 2 van 2)")
        mock_gateway_send.assert_called_with(
            to=format_phone_number("0643465651"), token=ANY
        )

        sent_token = mock_gateway_send.call_args[1]["token"]

        response = self.client.post(
            response._request.get_full_path(),
            follow=True,
            data={
                "add_phone_number_wizard_view-current_step": "verify",
                "verify-token": sent_token,
            },
        )
        self.user.refresh_from_db()

        self.assertEqual(self.user.phonenumber, "+31643465651")
        self.assertRedirects(response, str(settings.LOGIN_REDIRECT_URL))

    @patch("open_inwoner.accounts.gateways.gateway.send")
    def test_login_fails_with_different_phonenumbers(self, mock_gateway_send):
        self.user.phonenumber = ""
        self.user.save()

        response = self.client.post(
            reverse("login"),
            data={
                "next": "",
                "username": self.user.email,
                "password": "secret",
            },
            follow=True,
        )
        self.assertContains(response, "Account verificatie (stap 1 van 2)")
        mock_gateway_send.assert_not_called()

        response = self.client.post(
            response._request.get_full_path(),
            data={
                "add_phone_number_wizard_view-current_step": "phonenumber",
                "phonenumber-phonenumber_1": "0643465652",
                "phonenumber-phonenumber_2": "0643488882",
            },
            follow=True,
        )

        self.assertEqual(
            response.context["form"].errors,
            {"__all__": [_("De telefoonnummers komen niet overeen.")]},
        )
