from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from mozilla_django_oidc_db.models import OpenIDConnectConfig

from .factories import UserFactory

User = get_user_model()


class OIDCFlowTests(TestCase):
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(enabled=True),
    )
    def test_duplicate_email_unique_constraint_violated(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        """
        Assert that duplicate email addresses result in usable user feedback.
        """
        # set up a user with a colliding email address
        mock_get_userinfo.return_value = {
            "email": "collision@example.com",
            "sub": "some_username",
        }
        user = UserFactory.create(email="collision@example.com")
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("root"), fetch_redirect_response=False
        )
        self.assertTrue(User.objects.filter(oidc_id="some_username").exists())
        user.refresh_from_db()
        self.assertEqual(user.oidc_id, "some_username")
        db_user = User.objects.filter(oidc_id="some_username").first()
        self.assertEqual(db_user.id, user.id)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(enabled=True),
    )
    def test_happy_flow(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        """
        Assert that duplicate email addresses result in usable user feedback.
        """
        # set up a user with a colliding email address
        mock_get_userinfo.return_value = {
            "email": "nocollision@example.com",
            "sub": "some_username",
        }
        UserFactory.create(email="collision@example.com")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("root"), fetch_redirect_response=False
        )
        self.assertTrue(User.objects.filter(email="nocollision@example.com").exists())

    def test_error_page_direct_access_forbidden(self):
        error_url = reverse("admin-oidc-error")

        response = self.client.get(error_url)

        self.assertEqual(response.status_code, 403)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(enabled=True),
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "email": "nocollision@example.com",
            "sub": "some_username",
        }
        session = self.client.session
        session["oidc-error"] = "some error"
        session.save()
        error_url = reverse("admin-oidc-error")

        with self.subTest("with error"):
            response = self.client.get(error_url)

            self.assertEqual(response.status_code, 200)

        with self.subTest("after succesful login"):
            session["oidc_states"] = {"mock": {"nonce": "nonce"}}
            session.save()
            callback_url = reverse("oidc_authentication_callback")

            # enter the login flow
            callback_response = self.client.get(
                callback_url, {"code": "mock", "state": "mock"}
            )

            self.assertRedirects(
                callback_response, reverse("root"), fetch_redirect_response=False
            )

            with self.subTest("check error page again"):
                response = self.client.get(error_url)

                self.assertEqual(response.status_code, 403)
