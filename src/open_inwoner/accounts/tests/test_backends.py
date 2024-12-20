import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib import auth
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from freezegun import freeze_time
from furl import furl
from mozilla_django_oidc_db.config import store_config
from oath import totp

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory


class OIDCBackendTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "open_inwoner.accounts.backends.CustomOIDCBackend",
            "open_inwoner.accounts.backends.DigiDEHerkenningOIDCBackend",
        ]
    )
    @patch("open_inwoner.accounts.backends.DigiDEHerkenningOIDCBackend.authenticate")
    def test_digid_oidc_selects_correct_backend(self, mock_authenticate):
        """
        Both the regular OIDC and eHerkenning backend should check if the request path matches
        their callback before trying to authenticate
        """
        mock_authenticate.return_value = self.user

        init_response = self.client.get(reverse("digid_oidc:init"))

        assert "oidc_states" in self.client.session

        state = furl(init_response["Location"]).query.params["state"]
        nonce = self.client.session["oidc_states"][state]["nonce"]
        # set up a request
        callback_request = RequestFactory().get(
            reverse("digid_oidc:callback"),
            {"state": state, "nonce": nonce},
        )
        callback_request.session = self.client.session
        store_config(callback_request)

        result = auth.authenticate(callback_request)

        self.assertEqual(result, self.user)
        # django keeps track of which backend was used to authenticate
        self.assertEqual(
            result.backend, "open_inwoner.accounts.backends.DigiDEHerkenningOIDCBackend"
        )

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "open_inwoner.accounts.backends.DigiDEHerkenningOIDCBackend",
            "open_inwoner.accounts.backends.CustomOIDCBackend",
        ]
    )
    @patch(
        "mozilla_django_oidc_db.backends.BaseBackend.authenticate",
        side_effect=Exception,
    )
    @patch("open_inwoner.accounts.backends.CustomOIDCBackend.authenticate")
    def test_admin_oidc_selects_correct_backend(
        self, mock_authenticate, mock_digid_eherkenning_authenticate
    ):
        """
        Both the DigiD and eHerkenning backend should check if the request path matches
        their callback before trying to authenticate
        """
        mock_authenticate.return_value = self.user
        init_response = self.client.get(reverse("oidc_authentication_init"))
        assert "oidc_states" in self.client.session
        state = furl(init_response["Location"]).query.params["state"]
        nonce = self.client.session["oidc_states"][state]["nonce"]
        # set up a request
        callback_request = RequestFactory().get(
            reverse("oidc_authentication_callback"),
            {"state": state, "nonce": nonce},
        )
        callback_request.session = self.client.session
        store_config(callback_request)

        result = auth.authenticate(callback_request)

        self.assertEqual(result, self.user)
        self.assertEqual(
            result.backend, "open_inwoner.accounts.backends.CustomOIDCBackend"
        )


@override_settings(
    AUTHENTICATION_BACKENDS=[
        "open_inwoner.accounts.backends.UserModelEmailBackend",
    ]
)
class UserModelEmailBackendTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.password = "keepitsecert"
        cls.user = UserFactory(
            login_type=LoginTypeChoices.default, password=cls.password
        )
        for login_type in LoginTypeChoices:
            UserFactory(login_type=login_type)

    def test_duplicate_emails_on_case_results_in_no_match(self):
        request = RequestFactory().post(reverse("login"))

        UserFactory(email=self.user.email.upper(), login_type=self.user.login_type)
        result = auth.authenticate(
            request, username=self.user.email, password=self.password
        )
        self.assertEqual(result, None)

    def test_correct_username_password_return_user(self):
        request = RequestFactory().post(reverse("login"))

        result = auth.authenticate(
            request, username=self.user.email, password=self.password
        )
        self.assertEqual(result, self.user)

    def test_incorrect_username_password_return_none(self):
        request = RequestFactory().post(reverse("login"))

        for username, password in (
            (self.user.email, "incorrect"),
            ("incorrect", self.password),
        ):
            result = auth.authenticate(request, username=username, password=password)
            self.assertEqual(result, None)

    def test_missing_username_and_or_password_returns_none(self):
        for username in (self.user.email, "", None):
            for password in (self.password, "", None):
                if username and password:
                    # This is the successful case, exclude it, but ensure we
                    # also have permutations with one valid/one invalid value.
                    continue

                with self.subTest(f"{username=} {password=}"):
                    request = RequestFactory().post(reverse("login"))
                    result = auth.authenticate(
                        request, username=username, password=password
                    )
                    self.assertEqual(result, None)


@override_settings(
    AUTHENTICATION_BACKENDS=[
        "open_inwoner.accounts.backends.Verify2FATokenBackend",
    ]
)
class Verify2FATokenBackendTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory(login_type=LoginTypeChoices.default)
        cls.expires_in = getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300)
        cls.make_token = lambda: totp(cls.user.seed, period=cls.expires_in)

    @freeze_time("2023-05-22 12:05:01")
    def test_valid_token_and_user_returns_user(self):
        request = RequestFactory().get(reverse("verify_token"))

        result = auth.authenticate(request, user=self.user, token=self.make_token())
        self.assertEqual(result, self.user)

    def test_expired_token_and_valid_user_returns_none(self):
        request = RequestFactory().get(reverse("verify_token"))

        with freeze_time("2023-05-22 12:05:01") as ft:
            token = self.make_token()

            ft.tick(delta=datetime.timedelta(seconds=self.expires_in * 2))
            result = auth.authenticate(request, user=self.user, token=token)
            self.assertEqual(result, None)

    def test_missing_user_and_or_token_returns_none(self):
        for user in (self.user.email, "", None):
            for token in (self.make_token(), "", None):
                if user and token:
                    # This is the successful case, exclude it, but ensure we
                    # also have permutations with one valid/one invalid value.
                    continue

                with self.subTest(f"{user=} {token=}"):
                    request = RequestFactory().get(reverse("verify_token"))
                    result = auth.authenticate(request, user=user, token=token)
                    self.assertEqual(result, None)
