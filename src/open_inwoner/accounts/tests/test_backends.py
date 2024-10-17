from unittest.mock import patch

from django.contrib import auth
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from furl import furl
from mozilla_django_oidc_db.config import store_config

from .factories import UserFactory


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
