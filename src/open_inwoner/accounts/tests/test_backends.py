from unittest.mock import patch

from django.contrib import auth
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory


class OIDCBackendTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "open_inwoner.accounts.backends.CustomOIDCBackend",
            "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationEHerkenningBackend",
            "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationDigiDBackend",
        ]
    )
    @patch(
        "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationDigiDBackend.authenticate"
    )
    @patch(
        "open_inwoner.accounts.backends.OIDCAuthenticationBackend.authenticate",
        side_effect=Exception,
    )
    def test_digid_oidc_use_correct_backend(
        self, mock_authenticate, mock_digid_authenticate
    ):
        """
        Both the regular OIDC and eHerkenning backend should check if the request path matches
        their callback before trying to authenticate
        """
        mock_digid_authenticate.return_value = self.user

        request = RequestFactory().get(reverse("digid_oidc:callback"))

        result = auth.authenticate(request)

        self.assertEqual(result, self.user)

    @override_settings(
        AUTHENTICATION_BACKENDS=[
            "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationDigiDBackend",
            "digid_eherkenning_oidc_generics.backends.OIDCAuthenticationEHerkenningBackend",
            "open_inwoner.accounts.backends.CustomOIDCBackend",
        ]
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.authenticate",
        side_effect=Exception,
    )
    @patch("open_inwoner.accounts.backends.CustomOIDCBackend.authenticate")
    def test_admin_oidc_use_correct_backend(
        self, mock_authenticate, mock_digid_eherkenning_authenticate
    ):
        """
        Both the DigiD and eHerkenning backend should check if the request path matches
        their callback before trying to authenticate
        """
        mock_authenticate.return_value = self.user

        request = RequestFactory().get(reverse("oidc_authentication_callback"))

        result = auth.authenticate(request)

        self.assertEqual(result, self.user)
